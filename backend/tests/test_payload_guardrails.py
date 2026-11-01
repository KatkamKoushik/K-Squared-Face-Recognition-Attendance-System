"""
FRS V7.1 K² — Ingress Payload Size & Media Type Guardrail Tests.
Verifies pre-parsing bounds, 413 rejection, 415 media type enforcement,
and correlation ID propagation (Checklist Controls 28-N006, 28-B031, 28-B035).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_normal_payload_within_limit_accepted():
    """Confirms requests with normal size and valid media type pass through."""
    response = client.post(
        "/api/v1/academic/departments",
        json={"code": "CSE", "name": "Computer Science"},
        headers={"Content-Type": "application/json"},
    )
    # Expected 401 Unauthorized from auth gatekeeper, NOT 413 or 415
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


def test_oversized_payload_rejected_with_413():
    """Confirms oversized Content-Length is rejected before parsing with 413 (28-N006)."""
    # 20 MB payload exceeds MAX_UPLOAD_SIZE_MB (15 MB)
    oversized_bytes = 20 * 1024 * 1024
    response = client.post(
        "/api/v1/auth/login",
        content=b"{}",
        headers={
            "Content-Length": str(oversized_bytes),
            "Content-Type": "application/json",
            "X-Correlation-ID": "test-size-413",
        },
    )
    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert data["error"]["reason_code"] == "CONTENT_LENGTH_EXCEEDED"
    assert data["correlation_id"] == "test-size-413"


def test_prohibited_media_type_rejected_with_415():
    """Confirms dangerous/prohibited executable media types are rejected with 415."""
    response = client.post(
        "/api/v1/auth/login",
        content=b"echo dangerous",
        headers={
            "Content-Type": "application/x-sh",
            "X-Correlation-ID": "test-media-415",
        },
    )
    assert response.status_code == 415
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert data["error"]["reason_code"] == "PROHIBITED_MEDIA_TYPE"
    assert data["correlation_id"] == "test-media-415"


def test_get_requests_unaffected_by_payload_guardrail():
    """Confirms GET requests (e.g. health liveness) pass through normally."""
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ALIVE"
