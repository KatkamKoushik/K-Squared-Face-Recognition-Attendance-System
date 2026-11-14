"""
K² FRS — Security Hardening & Authentication Guard Tests.
Validates:
1. Query parameter authentication token rejection (preventing URL token leak in logs).
2. Bearer token requirement via Authorization header.
3. Correct role inheritance (SUB_ADMIN inherits FACULTY, but FACULTY cannot act as SUB_ADMIN).
4. Biometric demo endpoint authentication guard (SEC-02).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import create_application
from app.core.database import get_db
from app.core.security import create_access_token
from app.domain.enums import UserRole
from app.domain.models.academic import User, Department


@pytest.fixture
def test_client(db_session: Session):
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_token_query_param_rejected(test_client: TestClient, db_session: Session):
    """Verify that ?token=<jwt> in URL is rejected with HTTP 401 TOKEN_MISSING."""
    dept = Department(id=str(uuid.uuid4()), code="CSE_SEC", name="Computer Science", is_active=True)
    db_session.add(dept)
    db_session.flush()

    user = User(
        id=str(uuid.uuid4()),
        email="faculty_sec@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.FACULTY,
        department_id=dept.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        additional_claims={"email": user.email, "user_id": user.id},
    )

    # Passing token via query parameter must be rejected
    res_query = test_client.get(f"/api/v1/academic/departments?token={token}")
    assert res_query.status_code == 401
    data = res_query.json()
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"
    assert data["error"]["reason_code"] == "TOKEN_MISSING"

    # Passing token via Authorization header must succeed
    res_header = test_client.get("/api/v1/academic/departments", headers={"Authorization": f"Bearer {token}"})
    assert res_header.status_code == 200


def test_role_hierarchy_faculty_cannot_act_as_sub_admin(db_session: Session):
    """Verify that FACULTY does not satisfy SUB_ADMIN, but SUB_ADMIN satisfies FACULTY."""
    dept = Department(id=str(uuid.uuid4()), code="IT_SEC", name="Information Technology", is_active=True)
    db_session.add(dept)
    db_session.flush()

    faculty_user = User(
        id=str(uuid.uuid4()),
        email="fac_strict@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.FACULTY,
        department_id=dept.id,
        is_active=True,
    )
    sub_admin_user = User(
        id=str(uuid.uuid4()),
        email="subadmin_strict@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.SUB_ADMIN,
        department_id=dept.id,
        is_active=True,
    )
    db_session.add_all([faculty_user, sub_admin_user])
    db_session.commit()

    from app.api.dependencies import require_roles
    from app.core.errors import PermissionDeniedError

    sub_admin_guard = require_roles([UserRole.SUB_ADMIN])
    # 1. FACULTY user calling an endpoint requiring SUB_ADMIN must be rejected
    with pytest.raises(PermissionDeniedError) as exc_info:
        sub_admin_guard(faculty_user)
    assert exc_info.value.reason_code == "ROLE_NOT_AUTHORIZED"

    # 2. SUB_ADMIN user calling an endpoint requiring SUB_ADMIN must succeed
    assert sub_admin_guard(sub_admin_user).id == sub_admin_user.id

    # 3. SUB_ADMIN user calling an endpoint requiring FACULTY must be authorized (inheritance)
    faculty_guard = require_roles([UserRole.FACULTY])
    assert faculty_guard(sub_admin_user).id == sub_admin_user.id


def test_demo_biometric_endpoints_privacy_guard(test_client: TestClient, db_session, seed_data):
    """
    SEC-02: Public unauthenticated requests to /demo/enrolled-students and /demo/analyze
    must be rejected with HTTP 401 Unauthorized to protect institutional biometric records.
    Authenticated faculty callers succeed.
    """
    from app.domain.models.student import EnrollmentProfile

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
    db_session.commit()

    # 1. Unauthenticated request -> HTTP 401
    res_unauth = test_client.get("/api/v1/demo/enrolled-students")
    assert res_unauth.status_code == 401

    res_analyze_unauth = test_client.post("/api/v1/demo/analyze")
    assert res_analyze_unauth.status_code == 401

    # 2. Authenticated Faculty request -> HTTP 200
    from app.core.security import create_access_token
    faculty = seed_data["faculty_user"]
    token = create_access_token(
        subject=str(faculty.id),
        role=faculty.role.value,
        additional_claims={"email": faculty.email, "user_id": faculty.id},
    )
    res_auth = test_client.get(
        "/api/v1/demo/enrolled-students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_auth.status_code == 200
    data = res_auth.json()["data"]
    assert len(data) > 0
    for item in data:
        assert item["student_id"]
        assert not item["student_id"].startswith("anon_")
