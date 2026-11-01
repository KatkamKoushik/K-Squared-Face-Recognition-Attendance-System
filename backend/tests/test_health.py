"""
FRS V7.1 K² — Liveness & Readiness Route Handler Tests.
"""

from sqlalchemy.orm import Session
from app.api.v1.health import liveness_probe, readiness_probe, prometheus_metrics


def test_liveness_probe():
    response = liveness_probe()
    assert response.success is True
    assert response.data["status"] == "ALIVE"
    assert response.data["service"] == "FRS Control Plane"


def test_readiness_probe(db_session: Session):
    response = readiness_probe(db=db_session)
    assert response.success is True
    assert response.data["status"] == "READY"
    assert response.data["database"] == "CONNECTED"


def test_prometheus_metrics(db_session: Session):
    metrics_output = prometheus_metrics(db=db_session)
    assert "frs_uptime_seconds" in metrics_output
    assert 'frs_service_status{component="control_plane"} 1' in metrics_output
    assert 'frs_service_status{component="database"} 1' in metrics_output
    assert "frs_planned_units_invariant_verified 1" in metrics_output

