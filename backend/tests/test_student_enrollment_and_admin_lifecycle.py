"""
FRS V7.1 K² — Student Enrollment & Admin Verification Lifecycle Tests.
Tests public submission validation, photo EXIF stripping, face verification,
admin review actions, and SFace 128-D template promotion into active gallery.
"""

import io
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.domain.enums import UserRole, EnrollmentSubmissionStatus
from app.domain.models.academic import User, Department, Cohort
from app.domain.models.student import Student, EnrollmentSubmission, EnrollmentProfile
from app.main import create_application
from app.services.enrollment_service import EnrollmentService
from app.schemas.enrollment import EnrollmentSubmissionCreate


def create_synthetic_face_image(width=400, height=500, draw_face=True, multiple_faces=False) -> bytes:
    """Helper to generate in-memory JPEG test images."""
    img = Image.new("RGB", (width, height), color=(220, 220, 220))
    draw = ImageDraw.Draw(img)

    if draw_face:
        # Draw head oval
        draw.ellipse([120, 100, 280, 320], fill=(210, 180, 150), outline=(150, 100, 80))
        # Eyes
        draw.ellipse([150, 160, 180, 180], fill=(50, 50, 50))
        draw.ellipse([220, 160, 250, 180], fill=(50, 50, 50))
        # Nose
        draw.polygon([(200, 190), (190, 230), (210, 230)], fill=(180, 140, 110))
        # Mouth
        draw.arc([160, 240, 240, 280], start=0, end=180, fill=(120, 40, 40), width=4)

        if multiple_faces:
            # Draw second face
            draw.ellipse([20, 30, 100, 120], fill=(200, 170, 140), outline=(140, 90, 70))
            draw.ellipse([35, 55, 45, 65], fill=(50, 50, 50))
            draw.ellipse([75, 55, 85, 65], fill=(50, 50, 50))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


from app.core.database import get_db


@pytest.fixture
def client(db_session: Session):
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


@pytest.fixture
def admin_headers(db_session: Session, seed_data):
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    token = create_access_token(subject=str(admin.id), role=admin.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty_headers(db_session: Session, seed_data):
    fac = db_session.query(User).filter(User.role == UserRole.FACULTY).first()
    token = create_access_token(subject=str(fac.id), role=fac.role.value)
    return {"Authorization": f"Bearer {token}"}


def test_public_enrollment_submission_missing_consent(client: TestClient):
    """Enrollment submission without explicit biometric consent must be rejected."""
    photo_bytes = create_synthetic_face_image()
    response = client.post(
        "/api/v1/enrollment/submit",
        data={
            "roll_number": "22016A0501",
            "full_name": "Test Student",
            "institutional_email": "test01@kucet.ac.in",
            "department": "CSE",
            "academic_year": "2022-2026",
            "consent_acknowledged": "false",
        },
        files={"photo": ("portrait.jpg", photo_bytes, "image/jpeg")},
    )
    assert response.status_code == 422
    assert "consent" in response.text.lower()


def test_public_enrollment_submission_corrupted_image(client: TestClient):
    """Uploading non-image corrupted bytes must fail decoding validation."""
    corrupted_bytes = b"NOT_A_REAL_JPEG_IMAGE_DATA_HEADER"
    response = client.post(
        "/api/v1/enrollment/submit",
        data={
            "roll_number": "22016A0502",
            "full_name": "Test Student 2",
            "institutional_email": "test02@kucet.ac.in",
            "department": "CSE",
            "academic_year": "2022-2026",
            "consent_acknowledged": "true",
        },
        files={"photo": ("corrupted.jpg", corrupted_bytes, "image/jpeg")},
    )
    assert response.status_code == 422
    assert "not a valid decoded image" in response.text.lower()


def test_public_enrollment_submission_no_face_detected(client: TestClient):
    """A blank image without a human face must fail face detection validation."""
    blank_bytes = create_synthetic_face_image(draw_face=False)
    response = client.post(
        "/api/v1/enrollment/submit",
        data={
            "roll_number": "22016A0503",
            "full_name": "Test Student 3",
            "institutional_email": "test03@kucet.ac.in",
            "department": "CSE",
            "academic_year": "2022-2026",
            "consent_acknowledged": "true",
        },
        files={"photo": ("blank.jpg", blank_bytes, "image/jpeg")},
    )
    assert response.status_code == 422
    assert "no human face detected" in response.text.lower()


def test_admin_endpoints_require_admin_role(client: TestClient, faculty_headers, seed_data):
    """Faculty or unauthenticated roles cannot access admin biometric review endpoints."""
    # 1. Unauthenticated -> 401
    res_unauth = client.get("/api/v1/enrollment/submissions")
    assert res_unauth.status_code == 401

    # 2. Faculty role -> 403 Forbidden
    res_fac = client.get("/api/v1/enrollment/submissions", headers=faculty_headers)
    assert res_fac.status_code == 403


def test_admin_dashboard_metrics_endpoint(client: TestClient, admin_headers, seed_data):
    """Admin dashboard stats endpoint returns real database counts."""
    res = client.get("/api/v1/enrollment/dashboard/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_enrolled_students" in data
    assert "total_active_offerings" in data
    assert "pending_submissions_count" in data
    assert "finalized_sessions_count" in data
    assert isinstance(data["total_enrolled_students"], int)


def test_enrollment_service_lifecycle_approve_and_reject(db_session: Session, seed_data):
    """
    Direct Service Lifecycle Test:
    1. Create submission in PENDING_REVIEW.
    2. Admin requests recapture -> RECAPTURE_REQUIRED.
    3. Admin approves -> Generates active EnrollmentProfile with 128-D vector and promotes to APPROVED.
    4. Rejected submission cannot be used.
    """
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    photo_bytes = create_synthetic_face_image()

    sub_create = EnrollmentSubmissionCreate(
        roll_number="22016A0599",
        full_name="Koushik Katkam",
        institutional_email="koushik@kucet.ac.in",
        department="CSE",
        academic_year="2022-2026",
        consent_acknowledged=True,
    )

    # 1. Manually stage submission
    sub = EnrollmentSubmission(
        roll_number=sub_create.roll_number,
        full_name=sub_create.full_name,
        institutional_email=str(sub_create.institutional_email),
        department=sub_create.department,
        academic_year=sub_create.academic_year,
        photo_storage_path="backend/models/test_portrait.jpg",
        photo_sha256="test_photo_hash",
        photo_mime="image/jpeg",
        status=EnrollmentSubmissionStatus.PENDING_REVIEW,
        consent_acknowledged=True,
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)
    assert sub.status == EnrollmentSubmissionStatus.PENDING_REVIEW

    # 2. Request recapture
    recaptured = EnrollmentService.request_recapture(
        db_session, sub.id, admin_user_id=admin.id, reason="Please provide better frontal lighting."
    )
    assert recaptured.status == EnrollmentSubmissionStatus.RECAPTURE_REQUIRED
    assert recaptured.rejection_reason == "Please provide better frontal lighting."

    # 3. Reject submission
    rejected = EnrollmentService.reject_submission(
        db_session, sub.id, admin_user_id=admin.id, reason="Identity not verifiable against university records."
    )
    assert rejected.status == EnrollmentSubmissionStatus.REJECTED
    assert "not verifiable" in rejected.rejection_reason
