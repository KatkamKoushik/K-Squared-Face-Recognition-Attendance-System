"""
K² FRS — Fine-Tuned SFace (128-D) Database Embeddings Generator.
Processes all registered student enrollment faces in the database,
computes 128-D L2-normalized Fine-Tuned SFace embeddings,
and persists active EnrollmentProfile records with namespaces
'kucet_frs_sface_finetuned_v2' and 'kucet_frs_sface_finetuned_v3'.
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
from PIL import Image
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
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.services.enrollment_service import EnrollmentService
from app.worker.preprocessor import Preprocessor

MODEL_HASH = "e1bf5e2fd83ac6384d562680297451823145f83025aa0e6f2fb9199184205156"
NAMESPACES = ["kucet_frs_sface_finetuned_v2", "kucet_frs_sface_finetuned_v3"]
DIMENSION = 128


def run_extraction():
    print("=" * 70)
    print("K² FRS — Extracting Fine-Tuned SFace (128-D) Database Embeddings for All Faces")
    print("=" * 70)

    model_path = BACKEND_DIR / "models" / "kucet_frs_sface_finetuned.onnx"
    if not model_path.exists():
        raise FileNotFoundError(f"Model weights missing: {model_path}")

    print("Initializing YuNet detector and Fine-Tuned SFace recognizer...")
    detector = DetectorAdapter(strict_mode=True)
    recognizer = RecognizerAdapter(model_path=model_path, strict_mode=True)
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
                # Load image from Cloudinary or local storage
                image_bytes = CloudinaryStorageService.load_image_bytes(sub.photo_storage_path)
                arr = np.frombuffer(image_bytes, np.uint8)
                img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img_bgr is None:
                    print(f"[{idx}/{len(submissions)}] ERROR: Failed to decode photo for {roll}")
                    error_count += 1
                    continue

                pil_img = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
                dets = detector.detect_faces(pil_img)

                if not dets:
                    # Fallback to aspect-preserving center crop if no face detected
                    h, w = img_bgr.shape[:2]
                    min_dim = min(h, w)
                    sx = (w - min_dim) // 2
                    sy = (h - min_dim) // 2
                    crop_bgr = img_bgr[sy:sy + min_dim, sx:sx + min_dim]
                    crop_pil = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
                    conf = 0.50
                else:
                    primary_det = EnrollmentService._select_primary_face(dets)
                    crop_pil = Preprocessor.extract_face_crop(pil_img, primary_det.box)
                    conf = float(primary_det.score)

                emb_result = recognizer.compute_embedding(crop_pil)
                embedding = np.array(emb_result.vector, dtype=np.float32)
                norm = float(np.linalg.norm(embedding))
                if norm > 0:
                    embedding = embedding / norm

                vector_list = [round(float(v), 6) for v in embedding]

                # Persist to both v2 and v3 namespaces for backward & forward compatibility
                for ns in NAMESPACES:
                    existing = db.scalars(
                        select(EnrollmentProfile).where(
                            EnrollmentProfile.student_id == student.id,
                            EnrollmentProfile.embedding_namespace == ns,
                        )
                    ).first()

                    if existing:
                        existing.vector_data = vector_list
                        existing.embedding_dimension = DIMENSION
                        existing.model_artifact_id = MODEL_HASH
                        existing.is_active = True
                        existing.profile_version = getattr(existing, "profile_version", 1) + 1
                    else:
                        new_prof = EnrollmentProfile(
                            student_id=student.id,
                            model_artifact_id=MODEL_HASH,
                            embedding_namespace=ns,
                            embedding_dimension=DIMENSION,
                            vector_data=vector_list,
                            profile_version=1,
                            is_active=True,
                        )
                        db.add(new_prof)

                db.flush()

                extracted_profiles.append({
                    "student_id": str(student.id),
                    "roll_number": student.roll_number,
                    "full_name": student.full_name,
                    "vector": vector_list,
                    "norm": round(norm, 6),
                    "confidence": round(conf, 4),
                })

                success_count += 1
                print(f"[{idx}/{len(submissions)}] OK: {roll} ({student.full_name}) -> 128-D embedding extracted (conf={conf:.3f})")

            except Exception as e:
                db.rollback()
                print(f"[{idx}/{len(submissions)}] ERROR: {roll} -> {e}")
                error_count += 1

        db.commit()
        print("\n" + "=" * 70)
        print("DATABASE EMBEDDINGS EXTRACTION SUMMARY (FINE-TUNED SFACE 128-D)")
        print(f"  Total submissions processed : {len(submissions)}")
        print(f"  Successfully extracted      : {success_count}")
        print(f"  Skipped                     : {skipped_count}")
        print(f"  Errors                      : {error_count}")
        print("=" * 70)

        # Save JSON backup
        data_dir = BACKEND_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        out_json = data_dir / "finetuned_student_embeddings.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({
                "manifest_version": "7.2.0",
                "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "model_artifact_id": MODEL_HASH,
                "embedding_namespace": "kucet_frs_sface_finetuned_v2",
                "embedding_dimension": DIMENSION,
                "total_profiles": len(extracted_profiles),
                "profiles": extracted_profiles,
            }, f, indent=2)
        print(f"[OK] Saved backup JSON: {out_json} ({len(extracted_profiles)} profiles)")

    finally:
        db.close()


if __name__ == "__main__":
    run_extraction()
