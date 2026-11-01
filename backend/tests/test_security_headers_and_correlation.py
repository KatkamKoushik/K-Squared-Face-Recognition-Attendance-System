"""
FRS V7.1 K² — Security Headers & Correlation ID Middleware Test Suite.
Verifies compliance with OWASP Secure Headers and RFC 7807 correlation tracking.
"""

from starlette.testclient import TestClient
from app.main import create_application


def test_security_headers_present_on_all_responses():
    """All API responses must include defensive security headers."""
    app = create_application()
    client = TestClient(app)

    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert headers.get("Permissions-Policy") == "camera=(self), microphone=(), geolocation=()"


def test_correlation_id_propagated_when_provided():
    """If client sends X-Correlation-ID, backend preserves and echoes it."""
    app = create_application()
    client = TestClient(app)

    custom_corr_id = "test-corr-abc-12345"
    response = client.get(
        "/api/v1/health/liveness",
        headers={"X-Correlation-ID": custom_corr_id},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_corr_id


def test_correlation_id_generated_when_omitted():
    """If client does not send X-Correlation-ID, backend generates one with req- prefix."""
    app = create_application()
    client = TestClient(app)

    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    corr_id = response.headers.get("X-Correlation-ID")
    assert corr_id is not None
    assert corr_id.startswith("req-")
