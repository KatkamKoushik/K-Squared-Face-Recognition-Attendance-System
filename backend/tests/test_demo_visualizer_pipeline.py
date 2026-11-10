"""
FRS V7.1 K² — Universal Demo Testing & Visual Ground-Truth Pipeline Tests.
Validates branch-agnostic inference, face box overlay calculation, and three-tier reconciliation.
"""

import io
from PIL import Image, ImageDraw
import pytest
from fastapi.testclient import TestClient

from app.main import create_application
from app.core.database import get_db
from app.services.demo_service import DemoService
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.domain.models.student import Student, EnrollmentProfile, EnrollmentSubmission
from app.domain.enums import EnrollmentSubmissionStatus


@pytest.fixture
def client(db_session, seed_data):
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session

    student = seed_data["students"][0]
    profile = EnrollmentProfile(
        student_id=student.id,
        model_artifact_id="test_sface_model_sha256",
        embedding_namespace="sface_v1_kucet",
        embedding_dimension=128,
        vector_data=[0.05] * 128,
        profile_version=1,
        is_active=True,
    )
    db_session.add(profile)

    sub = EnrollmentSubmission(
        roll_number=student.roll_number,
        full_name=student.full_name,
        institutional_email=student.institutional_email or f"{student.roll_number.lower()}@kucet.ac.in",
        department="Computer Science",
        academic_year="2024-2028",
        photo_storage_path="/tmp/mock_photo.jpg",
        photo_sha256="abc1234",
        photo_mime="image/jpeg",
        status=EnrollmentSubmissionStatus.APPROVED,
        consent_acknowledged=True,
    )
    db_session.add(sub)
    db_session.commit()

    with TestClient(app) as test_client:
        yield test_client


def create_test_face_jpeg_bytes() -> bytes:
    """Generates a test JPEG with facial geometry for YuNet detection."""
    img = Image.new("RGB", (320, 320), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Head contour
    draw.ellipse([80, 50, 240, 250], fill=(215, 185, 155), outline=(140, 95, 75), width=2)
    # Eyes
    draw.ellipse([110, 110, 140, 130], fill=(40, 40, 40))
    draw.ellipse([180, 110, 210, 130], fill=(40, 40, 40))
    # Eyebrows
    draw.line([105, 98, 145, 102], fill=(40, 40, 40), width=3)
    draw.line([175, 102, 215, 98], fill=(40, 40, 40), width=3)
    # Nose
    draw.polygon([(160, 140), (150, 175), (170, 175)], fill=(185, 145, 115))
    # Mouth
    draw.ellipse([135, 195, 185, 215], fill=(160, 60, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_list_demo_enrolled_students(client: TestClient):
    """Verifies that the demo endpoint lists all enrolled student identities."""
    res = client.get("/api/v1/demo/enrolled-students")
    assert res.status_code == 200
    payload = res.json()
    assert "data" in payload
    data = payload["data"]
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "student_id" in first
    assert "roll_number" in first
    assert "full_name" in first


from unittest.mock import patch
from app.worker.contracts import DetectionResult


def test_analyze_demo_image_with_synthetic_face(client: TestClient):
    """Verifies that the demo analyze endpoint detects faces, returns normalized boxes, crops, and reconciliation."""
    img_bytes = create_test_face_jpeg_bytes()
    
    mock_detection = [
        DetectionResult(
            box=(0.25, 0.20, 0.75, 0.80),
            score=0.92,
            landmarks=[(0.35, 0.40), (0.65, 0.40), (0.50, 0.55), (0.40, 0.70), (0.60, 0.70)],
            raw_face=[80.0, 64.0, 160.0, 192.0, 112.0, 128.0, 208.0, 128.0, 160.0, 176.0, 128.0, 224.0, 192.0, 224.0, 0.92],
            detector_model_hash="8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        )
    ]

    with patch.object(DetectorAdapter, "detect_faces", return_value=mock_detection):
        res = client.post(
            "/api/v1/demo/analyze",
            files={"file": ("group_test.jpg", img_bytes, "image/jpeg")},
            data={"match_threshold": 0.363, "margin_threshold": 0.10, "blur_threshold": 20.0},
        )
    assert res.status_code == 200
    payload = res.json()["data"]
    assert "total_detected_faces" in payload
    assert "total_enrolled_students" in payload
    assert "detected_faces" in payload
    assert "attendance_granted" in payload
    assert "attendance_not_granted" in payload
    assert "unidentified_faces" in payload

    # Since the synthetic face does not match a real enrolled student, it is rejected as UNKNOWN_VISITOR (or MATCHED if similar)
    assert payload["total_detected_faces"] == 1
    face = payload["detected_faces"][0]
    assert "box" in face
    assert len(face["box"]) == 4
    x1, y1, x2, y2 = face["box"]
    assert x1 == 0.25 and y1 == 0.20 and x2 == 0.75 and y2 == 0.80
    assert face["face_crop_base64"].startswith("data:image/jpeg;base64,")
    assert face["color_hex"].startswith("#")
    assert len(face["badge_label"]) > 0
    assert face["face_crop_base64"].startswith("data:image/jpeg;base64,")
    assert face["color_hex"].startswith("#")
    assert len(face["badge_label"]) > 0


def test_analyze_demo_image_blank_returns_zero_detections(client: TestClient):
    """Verifies that a blank image with no human faces returns zero detections without errors."""
    blank = Image.new("RGB", (200, 200), color=(128, 128, 128))
    buf = io.BytesIO()
    blank.save(buf, format="JPEG")
    res = client.post(
        "/api/v1/demo/analyze",
        files={"file": ("blank.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert res.status_code == 200
    payload = res.json()["data"]
    assert payload["total_detected_faces"] == 0
    assert len(payload["detected_faces"]) == 0
    assert payload["present_count"] == 0
    assert payload["absent_count"] == payload["total_enrolled_students"]
