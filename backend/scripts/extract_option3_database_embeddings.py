"""
K² FRS — Option 3 (SCRFD-2.5G-KPS + OpenCV Zoo SFace) Database Embeddings Generator.
Processes all registered student enrollment faces in the database,
computes 128-D L2-normalized SFace embeddings with SCRFD 5-keypoint alignment,
and persists active EnrollmentProfile records with namespace 'sface_128d_v1'.
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
from benchmark import SCRFDDetector, SFaceRecognizer

MODEL_HASH = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
DETECTOR_HASH = "041f73f47371333d1d17a6fee6c8ab4e6aecabefe398ff32cca4e2d5eaee0af9"
NAMESPACE = "sface_128d_v1"
DIMENSION = 128


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
    print("K² FRS — Extracting Option 3 (SCRFD-2.5G + SFace 128-D) Database Embeddings")
    print("=" * 70)

    det_path = BACKEND_DIR / "models" / "scrfd_2.5g_kps.onnx"
    rec_path = BACKEND_DIR / "models" / "face_recognition_sface_2021dec.onnx"

    if not det_path.exists() or not rec_path.exists():
        raise FileNotFoundError(f"Model weights missing in {BACKEND_DIR / 'models'}")

    print("Initializing SCRFD-2.5G-KPS detector and SFace recognizer...")
    detector = SCRFDDetector(str(det_path), num_threads=2)
    recognizer = SFaceRecognizer(str(rec_path), num_threads=2)
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
                # Load image from Cloudinary or local path
                image_bytes = CloudinaryStorageService.load_image_bytes(sub.photo_storage_path)
                img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    print(f"[{idx}/{len(submissions)}] ERROR: Failed to decode photo for {roll}")
                    error_count += 1
                    continue

                # Detect faces using SCRFD-2.5G
                boxes, scores, kpss, _ = detector.detect(img, target_size=640, score_thresh=0.20)
                if len(boxes) == 0:
                    # Retry at 1280 resolution
                    boxes, scores, kpss, _ = detector.detect(img, target_size=1280, score_thresh=0.15)

                if len(boxes) == 0:
                    print(f"[{idx}/{len(submissions)}] WARN: No face detected for {roll}")
                    error_count += 1
                    continue

                best_idx = select_primary_face(boxes, scores, kpss, img.shape)
                best_kps = kpss[best_idx]
                best_box = boxes[best_idx]
                best_score = float(scores[best_idx])

                # Extract 128-D normalized embedding
                embedding = recognizer.align_and_extract(img, best_kps, bbox=best_box, score=best_score)
                norm = float(np.linalg.norm(embedding))

                if abs(norm - 1.0) > 1e-4:
                    embedding = embedding / norm

                vector_list = [round(float(v), 6) for v in embedding]

                # Insert or update EnrollmentProfile in PostgreSQL
                existing = db.scalars(
                    select(EnrollmentProfile).where(
                        EnrollmentProfile.student_id == student.id,
                        EnrollmentProfile.embedding_namespace == NAMESPACE,
                    )
                ).first()

                if existing:
                    existing.vector_data = vector_list
                    existing.embedding_dimension = DIMENSION
                    existing.model_artifact_id = MODEL_HASH
                    existing.is_active = True
                    existing.profile_version = getattr(existing, "profile_version", 1) + 1
                    action = "UPDATED"
                else:
                    new_prof = EnrollmentProfile(
                        student_id=student.id,
                        model_artifact_id=MODEL_HASH,
                        embedding_namespace=NAMESPACE,
                        embedding_dimension=DIMENSION,
                        vector_data=vector_list,
                        profile_version=1,
                        is_active=True,
                    )
                    db.add(new_prof)
                    action = "INSERTED"

                db.flush()

                extracted_profiles.append({
                    "student_id": str(student.id),
                    "roll_number": student.roll_number,
                    "full_name": student.full_name,
                    "vector": vector_list,
                    "norm": round(norm, 6),
                    "confidence": round(best_score, 4),
                })

                success_count += 1
                print(f"[{idx}/{len(submissions)}] {action}: {roll} ({student.full_name}) -> 128-D embedding extracted (norm={norm:.4f}, conf={best_score:.3f})")

            except Exception as e:
                db.rollback()
                print(f"[{idx}/{len(submissions)}] ERROR: {roll} -> {e}")
                error_count += 1

        db.commit()
        print("\n" + "=" * 70)
        print("DATABASE EMBEDDINGS EXTRACTION SUMMARY (OPTION 3 - SFace 128-D)")
        print(f"  Total submissions processed : {len(submissions)}")
        print(f"  Successfully extracted      : {success_count}")
        print(f"  Skipped                     : {skipped_count}")
        print(f"  Errors                      : {error_count}")
        print("=" * 70)

        # Save JSON backup
        data_dir = BACKEND_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        out_json = data_dir / "option3_student_embeddings.json"
        with open(out_json, "w") as f:
            json.dump({
                "model": "SCRFD-2.5G + OpenCV SFace",
                "namespace": NAMESPACE,
                "dimension": DIMENSION,
                "model_hash": MODEL_HASH,
                "count": len(extracted_profiles),
                "profiles": extracted_profiles,
            }, f, indent=2)
        print(f"\nSaved {len(extracted_profiles)} student embeddings to {out_json}")

    finally:
        db.close()


if __name__ == "__main__":
    run_extraction()
