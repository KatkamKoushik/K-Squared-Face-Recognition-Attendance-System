#!/usr/bin/env python3
"""
K² FRS — Real Student Face Enrollment CLI Tool (P0-C, P0-E).
Enrolls real volunteer reference photographs into PostgreSQL using verified
YuNet face detection, 5-landmark SFace alignment, and L2-normalized 128-D embeddings.
"""

import argparse
import sys
from pathlib import Path
import numpy as np
from PIL import Image

# Add backend directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.domain.models.student import Student, EnrollmentProfile
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from sqlalchemy import select


def enroll_face(roll_number: str, image_path: Path):
    if not image_path.is_file():
        print(f"[ERROR] Reference image file does not exist: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"=== K² FRS Biometric Volunteer Face Enrollment ===")
    print(f"Target Roll Number : {roll_number}")
    print(f"Reference Image    : {image_path}")

    # 1. Load image
    try:
        pil_img = Image.open(image_path).convert("RGB")
        w, h = pil_img.size
        print(f"[INFO] Loaded reference image: {w}x{h} px")
    except Exception as e:
        print(f"[ERROR] Failed to decode image: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Detect face using YuNet
    detector = DetectorAdapter(strict_mode=True)
    detections = detector.detect_faces(pil_img)

    if not detections:
        print("[ERROR] No face detected in the provided image. Please provide a clear, well-lit portrait.", file=sys.stderr)
        sys.exit(1)

    # Select primary face (highest score)
    best_det = max(detections, key=lambda d: d.score)
    print(f"[INFO] Detected primary face: score={best_det.score:.3f}, box={best_det.box}")

    # 3. Extract 128-D embedding with 5-landmark alignment
    import cv2
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    recognizer = RecognizerAdapter(strict_mode=True)

    if best_det.raw_face is not None:
        print("[INFO] Computing 5-landmark aligned SFace 128-D embedding (FaceRecognizerSF.alignCrop)...")
        emb = recognizer.align_and_compute_embedding(cv_img, best_det.raw_face)
    else:
        from app.worker.preprocessor import Preprocessor
        crop = Preprocessor.extract_face_crop(pil_img, best_det.box)
        emb = recognizer.compute_embedding(crop)

    print(f"[INFO] Generated L2-normalized 128-D embedding vector. (norm={np.linalg.norm(emb.vector):.4f})")

    # 4. Save to PostgreSQL
    with SessionLocal() as db:
        student = db.execute(select(Student).where(Student.roll_number == roll_number)).scalar_one_or_none()
        if not student:
            print(f"[WARN] Student with roll number {roll_number} not found in database. Listing available students:")
            students = db.execute(select(Student.roll_number, Student.full_name)).all()
            for r, name in students:
                print(f"  - {r}: {name}")
            print(f"[ERROR] Cannot enroll biometric profile for non-existent student: {roll_number}", file=sys.stderr)
            sys.exit(1)

        print(f"[INFO] Matching student: {student.full_name} ({student.roll_number})")

        # Find or create profile
        profile = db.execute(
            select(EnrollmentProfile).where(
                EnrollmentProfile.student_id == student.id,
                EnrollmentProfile.embedding_namespace == emb.namespace,
            )
        ).scalar_one_or_none()

        import uuid
        if not profile:
            profile = EnrollmentProfile(
                id=str(uuid.uuid4()),
                student_id=student.id,
                model_artifact_id=emb.recognizer_model_hash,
                embedding_namespace=emb.namespace,
                embedding_dimension=emb.dimension,
                vector_data=emb.vector,
                profile_version=1,
                is_active=True,
            )
            db.add(profile)
        else:
            profile.vector_data = emb.vector
            profile.model_artifact_id = emb.recognizer_model_hash
            profile.profile_version += 1
            profile.is_active = True

        db.commit()
        print(f"[SUCCESS] Successfully enrolled {student.full_name} ({student.roll_number})!")
        print(f"          Profile Version: {profile.profile_version}")
        print(f"          Model Hash     : {profile.model_artifact_id[:16]}...")
        print(f"          Namespace      : {profile.embedding_namespace}")


def main():
    parser = argparse.ArgumentParser(description="K² FRS Real Volunteer Face Enrollment Tool")
    parser.add_argument("--roll", required=True, help="Student roll number (e.g. 00622501)")
    parser.add_argument("--image", required=True, type=Path, help="Path to reference face image (JPG/PNG)")
    args = parser.parse_args()

    enroll_face(args.roll, args.image)


if __name__ == "__main__":
    main()
