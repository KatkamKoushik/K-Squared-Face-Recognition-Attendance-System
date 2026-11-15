"""
K² FRS — Direct Mobile Biometric Student Enrollment Test Suite.
Verifies immediate single-click mobile enrollment:
- Instant enrollment without two-step staging review
- Cloudinary photo upload to k2_frs/enrollments
- Separate multi-model embeddings extraction for:
  * Option 1 (512-D ArcFace, mobilefacenet_512d_v1)
  * Option 3 (128-D SFace, sface_128d_v1)
  * Fine-Tuned (128-D SFace, kucet_frs_sface_finetuned_v2)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.database import SessionLocal
from app.domain.models.student import Student, EnrollmentProfile, EnrollmentSubmission
from app.services.storage_service import CloudinaryStorageService
from app.services.enrollment_service import EnrollmentService

client = TestClient(app)


def test_mobile_direct_enroll_endpoint():
    db = SessionLocal()
    test_roll = "TEST_MOB_DIR_001"
    try:
        # 1. Fetch valid reference face bytes from an existing portrait in DB
        sample_sub = db.scalars(
            select(EnrollmentSubmission).where(EnrollmentSubmission.photo_storage_path.isnot(None))
        ).first()
        assert sample_sub is not None, "Need at least one existing submission to test portrait bytes"
        img_bytes = CloudinaryStorageService.load_image_bytes(sample_sub.photo_storage_path)
        assert len(img_bytes) > 1000

        # 2. Invoke POST /api/v1/enrollment/mobile/direct-enroll
        response = client.post(
            "/api/v1/enrollment/mobile/direct-enroll",
            data={
                "roll_number": test_roll,
                "full_name": "Koushik Katkam Direct",
                "department": "CSE",
                "academic_year": "2023-2027",
                "institutional_email": "koushik_direct@kucet.ac.in",
            },
            files={
                "photo": ("koushik_face.jpg", img_bytes, "image/jpeg"),
            },
        )
        assert response.status_code == 201, f"Failed: {response.text}"
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["roll_number"] == test_roll
        assert data["full_name"] == "Koushik Katkam Direct"
        assert "cloudinary" in data["cloudinary_photo_url"].lower() or "http" in data["cloudinary_photo_url"].lower()
        assert "Option 1 (512-D ArcFace)" in data["models_enrolled"]
        assert "Option 3 (128-D SFace)" in data["models_enrolled"]
        assert "Fine-Tuned SFace (128-D)" in data["models_enrolled"]
        assert "mobilefacenet_512d_v1" in data["namespaces"]
        assert "sface_128d_v1" in data["namespaces"]
        assert "kucet_frs_sface_finetuned_v2" in data["namespaces"]

        # 3. Verify PostgreSQL database records
        student = db.scalars(select(Student).where(Student.roll_number == test_roll)).first()
        assert student is not None
        assert student.is_active is True
        assert student.full_name == "Koushik Katkam Direct"

        sub = db.scalars(select(EnrollmentSubmission).where(EnrollmentSubmission.roll_number == test_roll)).first()
        assert sub is not None
        assert sub.status.value == "APPROVED" if hasattr(sub.status, "value") else sub.status == "APPROVED"
        assert sub.photo_storage_path == data["cloudinary_photo_url"]

        profiles = db.scalars(
            select(EnrollmentProfile).where(EnrollmentProfile.student_id == student.id)
        ).all()
        assert len(profiles) == 3
        namespaces_found = {p.embedding_namespace for p in profiles}
        assert "mobilefacenet_512d_v1" in namespaces_found
        assert "sface_128d_v1" in namespaces_found
        assert "kucet_frs_sface_finetuned_v2" in namespaces_found

        for p in profiles:
            assert p.is_active is True
            if p.embedding_namespace == "mobilefacenet_512d_v1":
                assert p.embedding_dimension == 512
                assert len(p.vector_data) == 512
            else:
                assert p.embedding_dimension == 128
                assert len(p.vector_data) == 128

    finally:
        # Cleanup test student
        st = db.scalars(select(Student).where(Student.roll_number == test_roll)).first()
        if st:
            db.query(EnrollmentProfile).filter(EnrollmentProfile.student_id == st.id).delete()
            db.query(EnrollmentSubmission).filter(EnrollmentSubmission.roll_number == test_roll).delete()
            db.delete(st)
            db.commit()
        db.close()
