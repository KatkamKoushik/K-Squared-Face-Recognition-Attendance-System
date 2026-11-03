"""
FRS V7.1 K² — Academic Core Hierarchy Endpoints Test Suite.
Verifies GET endpoints for departments, cohorts, terms, offerings, groups, and students.
Validates both unauthenticated rejection (401) and authorized ingestion (200).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_application
from app.core.database import get_db
from app.core.security import create_access_token


@pytest.fixture
def auth_client(db_session, seed_data):
    """Provides a TestClient with database session overridden and admin auth token."""
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session

    admin_user = seed_data["admin_user"]
    token = create_access_token(subject=str(admin_user.id), role="ADMIN")

    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_unauthenticated_requests_rejected():
    """Unauthenticated access must be strictly rejected with 401 Unauthorized."""
    app = create_application()
    unauth_client = TestClient(app)

    endpoints = [
        "/api/v1/academic/departments",
        "/api/v1/academic/cohorts",
        "/api/v1/academic/terms",
        "/api/v1/academic/offerings",
        "/api/v1/academic/groups",
        "/api/v1/academic/students",
    ]
    for ep in endpoints:
        resp = unauth_client.get(ep)
        assert resp.status_code == 401


def test_academic_departments_endpoint(auth_client):
    response = auth_client.get("/api/v1/academic/departments")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    dept = data["data"][0]
    assert dept["code"] == "CSE"


def test_academic_cohorts_endpoint(auth_client):
    response = auth_client.get("/api/v1/academic/cohorts")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 2


def test_academic_terms_endpoint(auth_client):
    response = auth_client.get("/api/v1/academic/terms")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_academic_offerings_endpoint(auth_client):
    response = auth_client.get("/api/v1/academic/offerings")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_academic_groups_endpoint(auth_client):
    response = auth_client.get("/api/v1/academic/groups")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_academic_students_endpoint(auth_client):
    response = auth_client.get("/api/v1/academic/students")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3
    rolls = [s["roll_number"] for s in data["data"]]
    assert "23CSE01" in rolls
