"""
K² FRS — Option 1 (SCRFD-500M-KPS + ArcFace MobileFaceNet) Database Embeddings Generator.
Processes all registered student enrollment faces in the database,
computes 512-D L2-normalized ArcFace embeddings with 5-keypoint affine alignment,
and persists active EnrollmentProfile records with namespace 'mobilefacenet_512d_v1'.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

# Add paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
LAB_DIR = Path("D:/K2-local-model-lab")
if LAB_DIR.exists():
    sys.path.insert(0, str(LAB_DIR))

from app.core.database import SessionLocal
from app.domain.models.student import Student, EnrollmentProfile, EnrollmentSubmission
from app.services.storage_service import CloudinaryStorageService
from benchmark import SCRFDDetector, ArcFaceRecognizer

MODEL_HASH = "9cc6e4a75f0e2bf0b1aed94578f144d15175f357bdc05e815e5c4a02b319eb4f"
NAMESPACE = "mobilefacenet_512d_v1"
DIMENSION = 512


def select_primary_face(boxes: np.ndarray, scores: np.ndarray, kpss: np.ndarray, img_shape: tuple) -> int:
    """Select the primary subject face based on area, centrality, and confidence."""
    if len(boxes) == 1:
        return 0

    h, w = img_shape[:2]
    best_idx = 0
    max_rank = -1.0

    for i in range(len(boxes)):
        bw = boxes[i, 2] - boxes[i, 0]
        bh = boxes[i, 3] - boxes[i, 1]
        area = max(0.0, bw * bh)
        cx = (boxes[i, 0] + boxes[i, 2]) / (2.0 * w)
        cy = (boxes[i, 1] + boxes[i, 3]) / (2.0 * h)
        dist = np.sqrt((cx - 0.5) ** 2 + (cy - 0.5) ** 2)
        centrality = max(0.2, 1.0 - dist)
        score = max(0.1, float(scores[i]))
        rank = area * centrality * (score ** 0.5)
        if rank > max_rank:
            max_rank = rank
            best_idx = i

    return best_idx


def run_extraction():
    print("=" * 70)
    print("K² FRS — Extracting Option 1 (ArcFace 512-D) Embeddings for Database Faces")
    print("=" * 70)

    det_path = BACKEND_DIR / "models" / "scrfd_500m_kps.onnx"
    rec_path = BACKEND_DIR / "models" / "mobilefacenet_w600k.onnx"

    if not det_path.exists() or not rec_path.exists():
        raise FileNotFoundError(f"Model weights missing in {BACKEND_DIR / 'models'}")

    print("Initializing SCRFD-500M-KPS detector and MobileFaceNet recognizer...")
    detector = SCRFDDetector(str(det_path), num_threads=2)
    recognizer = ArcFaceRecognizer(str(rec_path), num_threads=2)
    print("Models initialized successfully.")

    db: Session = SessionLocal()
    try:
        submissions = db.scalars(
            select(EnrollmentSubmission).where(EnrollmentSubmission.photo_storage_path.isnot(None))
        ).all()
        print(f"\nFound {len(submissions)} enrollment submissions with photo paths in database.")

        students_by_roll = {
            s.roll_number.strip().upper(): s
            for s in db.scalars(select(Student)).all()
        }

        success_count = 0
        skipped_count = 0
        error_count = 0
        extracted_profiles = []

        for idx, sub in enumerate(submissions, 1):
            roll = sub.roll_number.strip().upper()
            student = students_by_roll.get(roll)

            if not student:
                print(f"[{idx}/{len(submissions)}] SKIP: No student record for roll '{roll}'")
                skipped_count += 1
                continue

            try:
                # Load image
                image_bytes = CloudinaryStorageService.load_image_bytes(sub.photo_storage_path)
                img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    print(f"[{idx}/{len(submissions)}] ERROR: Failed to decode image for {roll}")
                    error_count += 1
                    continue

                # Detect faces
                boxes, scores, kpss, t_det = detector.detect(img, target_size=640, score_thresh=0.3)
                if len(boxes) == 0:
                    # Retry at 1280
                    boxes, scores, kpss, t_det = detector.detect(img, target_size=1280, score_thresh=0.25)

                if len(boxes) == 0:
                    print(f"[{idx}/{len(submissions)}] FAIL: No face detected in portrait for {roll}")
                    error_count += 1
                    continue

                best_idx = select_primary_face(boxes, scores, kpss, img.shape)
                emb = recognizer.align_and_extract(img, kpss[best_idx])

                norm = float(np.linalg.norm(emb))
                if abs(norm - 1.0) > 1e-3:
                    emb = emb / (norm + 1e-9)

                # Upsert EnrollmentProfile in database
                existing_profile = db.execute(
                    select(EnrollmentProfile).where(
                        EnrollmentProfile.student_id == student.id,
                        EnrollmentProfile.embedding_namespace == NAMESPACE,
                    )
                ).scalar_one_or_none()

                vector_list = [round(float(v), 6) for v in emb]

                if existing_profile:
                    existing_profile.vector_data = vector_list
                    existing_profile.model_artifact_id = MODEL_HASH
                    existing_profile.embedding_dimension = DIMENSION
                    existing_profile.is_active = True
                    existing_profile.profile_version += 1
                    action = "UPDATED"
                else:
                    new_profile = EnrollmentProfile(
                        student_id=student.id,
                        model_artifact_id=MODEL_HASH,
                        embedding_namespace=NAMESPACE,
                        embedding_dimension=DIMENSION,
                        vector_data=vector_list,
                        profile_version=1,
                        is_active=True,
                    )
                    db.add(new_profile)
                    action = "INSERTED"

                db.flush()
                success_count += 1
                extracted_profiles.append({
                    "roll_number": roll,
                    "student_id": student.id,
                    "full_name": student.full_name,
                    "confidence": round(float(scores[best_idx]), 3),
                    "vector": vector_list,
                })

                print(f"[{idx}/{len(submissions)}] {action} {roll} ({student.full_name}): 512-D vector (norm={norm:.4f}, conf={scores[best_idx]:.2f}, {t_det:.1f}ms)")

            except Exception as e:
                print(f"[{idx}/{len(submissions)}] EXCEPTION for {roll}: {e}")
                error_count += 1

        db.commit()
        print("\n" + "=" * 70)
        print(f"DATABASE PERSISTENCE COMPLETE:")
        print(f"  Successfully processed : {success_count}")
        print(f"  Skipped (no student)   : {skipped_count}")
        print(f"  Errors / No Face       : {error_count}")
        print(f"  Total Submissions      : {len(submissions)}")
        print("=" * 70)

        # Export local JSON backup
        data_dir = BACKEND_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        backup_file = data_dir / "option1_student_embeddings.json"
        with open(backup_file, "w") as f:
            json.dump({
                "model": "mobilefacenet_w600k",
                "namespace": NAMESPACE,
                "dimension": DIMENSION,
                "model_artifact_id": MODEL_HASH,
                "count": len(extracted_profiles),
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "students": extracted_profiles,
            }, f, indent=2)
        print(f"Exported local vector backup to: {backup_file}")

    finally:
        db.close()


if __name__ == "__main__":
    run_extraction()
