"""
FRS V7.1 K² — 5-Tier Hierarchical RBAC & Department Isolation Test Suite.
Validates the institutional access control hierarchy:
DEVELOPER > SUPER_ADMIN > ADMIN > SUB_ADMIN (FACULTY) > STUDENT

Enforces strict department-boundary invariants:
An administrator for CSE must NOT access, create, or review ECE or other departments' records.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import create_application
from app.core.database import get_db
from app.core.security import create_access_token
from app.domain.enums import UserRole, AcademicTerm
from app.domain.models.academic import User, Department, Cohort, Subject, AcademicYear, Term
from app.domain.models.student import Student


@pytest.fixture
def rbac_fixture(db_session: Session):
    """Sets up a controlled two-department institutional environment (CSE and ECE)."""
    # 1. Create CSE & ECE Departments
    cse_dept = Department(id=str(uuid.uuid4()), code="CSE", name="Computer Science & Engineering", is_active=True)
    ece_dept = Department(id=str(uuid.uuid4()), code="ECE", name="Electronics & Communication Engineering", is_active=True)
    db_session.add_all([cse_dept, ece_dept])
    db_session.flush()

    # 2. Create Cohorts for CSE and ECE
    cse_cohort = Cohort(
        id=str(uuid.uuid4()),
        department_id=cse_dept.id,
        name="CSE-2023-2027",
        admission_year=2023,
        graduation_year=2027,
        is_active=True,
    )
    ece_cohort = Cohort(
        id=str(uuid.uuid4()),
        department_id=ece_dept.id,
        name="ECE-2023-2027",
        admission_year=2023,
        graduation_year=2027,
        is_active=True,
    )
    db_session.add_all([cse_cohort, ece_cohort])
    db_session.flush()

    # 3. Create Students in each cohort
    cse_student = Student(
        id=str(uuid.uuid4()),
        roll_number="CSE001",
        full_name="CSE Student",
        institutional_email="cse001@kucet.ac.in",
        cohort_id=cse_cohort.id,
        is_active=True,
    )
    ece_student = Student(
        id=str(uuid.uuid4()),
        roll_number="ECE001",
        full_name="ECE Student",
        institutional_email="ece001@kucet.ac.in",
        cohort_id=ece_cohort.id,
        is_active=True,
    )
    db_session.add_all([cse_student, ece_student])
    db_session.flush()

    # 4. Create Users for each tier
    super_admin_user = User(
        id=str(uuid.uuid4()),
        email="super.admin@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.SUPER_ADMIN,
        department_id=None,
        is_active=True,
    )
    cse_admin_user = User(
        id=str(uuid.uuid4()),
        email="hod.cse@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.ADMIN,
        department_id=cse_dept.id,
        is_active=True,
    )
    ece_admin_user = User(
        id=str(uuid.uuid4()),
        email="hod.ece@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.ADMIN,
        department_id=ece_dept.id,
        is_active=True,
    )
    student_user = User(
        id=str(uuid.uuid4()),
        email="cse001@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.STUDENT,
        department_id=cse_dept.id,
        is_active=True,
    )
    developer_user = User(
        id=str(uuid.uuid4()),
        email="developer@frs.kucet.ac.in",
        hashed_password="hash",
        role=UserRole.DEVELOPER,
        department_id=None,
        is_active=True,
    )
    db_session.add_all([super_admin_user, cse_admin_user, ece_admin_user, student_user, developer_user])
    db_session.commit()

    return {
        "cse_dept": cse_dept,
        "ece_dept": ece_dept,
        "cse_cohort": cse_cohort,
        "ece_cohort": ece_cohort,
        "cse_student": cse_student,
        "ece_student": ece_student,
        "super_admin_user": super_admin_user,
        "cse_admin_user": cse_admin_user,
        "ece_admin_user": ece_admin_user,
        "student_user": student_user,
        "developer_user": developer_user,
    }


def make_client(db_session: Session, user: User) -> TestClient:
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    token = create_access_token(subject=str(user.id), role=user.role.value)
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_super_admin_can_manage_departments_and_institution(db_session: Session, rbac_fixture: dict):
    """Super Admin is the highest authority and can create departments and global calendar."""
    client = make_client(db_session, rbac_fixture["super_admin_user"])

    # 1. Create a new department
    res = client.post("/api/v1/academic/departments", json={"code": "MECH", "name": "Mechanical Engineering"})
    assert res.status_code == 201
    assert res.json()["data"]["code"] == "MECH"

    # 2. View all departments
    list_res = client.get("/api/v1/academic/departments")
    assert list_res.status_code == 200
    dept_codes = [d["code"] for d in list_res.json()["data"]]
    assert "CSE" in dept_codes and "ECE" in dept_codes and "MECH" in dept_codes


def test_department_admin_cannot_create_department_or_academic_year(db_session: Session, rbac_fixture: dict):
    """Department Admin does NOT have institutional authority to create departments or academic calendars."""
    client = make_client(db_session, rbac_fixture["cse_admin_user"])

    # Attempt to create department -> 403 Forbidden
    res = client.post("/api/v1/academic/departments", json={"code": "CIVIL", "name": "Civil Engineering"})
    assert res.status_code == 403
    assert res.json()["error"]["reason_code"] == "ROLE_NOT_AUTHORIZED"


def test_department_admin_isolation_on_cohorts(db_session: Session, rbac_fixture: dict):
    """CSE Admin can only view and create CSE cohorts; cannot access or create ECE cohorts."""
    client = make_client(db_session, rbac_fixture["cse_admin_user"])
    ece_dept_id = rbac_fixture["ece_dept"].id
    cse_dept_id = rbac_fixture["cse_dept"].id

    # 1. Listing cohorts automatically filters to CSE cohorts
    cohorts_res = client.get("/api/v1/academic/cohorts")
    assert cohorts_res.status_code == 200
    cohort_names = [c["name"] for c in cohorts_res.json()["data"]]
    assert "CSE-2023-2027" in cohort_names
    assert "ECE-2023-2027" not in cohort_names

    # 2. Attempting to explicitly query ECE department cohorts -> 403 Forbidden
    cross_res = client.get(f"/api/v1/academic/cohorts?department_id={ece_dept_id}")
    assert cross_res.status_code == 403
    assert cross_res.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 3. Attempting to create an ECE cohort -> 403 Forbidden
    create_cross = client.post(
        "/api/v1/academic/cohorts",
        json={"name": "ECE-2024-2028", "department_id": ece_dept_id, "admission_year": 2024, "graduation_year": 2028},
    )
    assert create_cross.status_code == 403
    assert create_cross.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 4. Creating a CSE cohort succeeds
    create_cse = client.post(
        "/api/v1/academic/cohorts",
        json={"name": "CSE-2024-2028", "department_id": cse_dept_id, "admission_year": 2024, "graduation_year": 2028},
    )
    assert create_cse.status_code == 201


def test_department_admin_isolation_on_students(db_session: Session, rbac_fixture: dict):
    """CSE Admin cannot view or register students in another department."""
    client = make_client(db_session, rbac_fixture["cse_admin_user"])
    ece_cohort_id = rbac_fixture["ece_cohort"].id
    cse_cohort_id = rbac_fixture["cse_cohort"].id

    # 1. Listing students returns only CSE students
    students_res = client.get("/api/v1/academic/students")
    assert students_res.status_code == 200
    rolls = [s["roll_number"] for s in students_res.json()["data"]]
    assert "CSE001" in rolls
    assert "ECE001" not in rolls

    # 2. Attempting to query students with an ECE cohort_id -> 403 Forbidden
    cross_cohort_query = client.get(f"/api/v1/academic/students?cohort_id={ece_cohort_id}")
    assert cross_cohort_query.status_code == 403
    assert cross_cohort_query.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 3. Attempting to register a student into an ECE cohort -> 403 Forbidden
    cross_create = client.post(
        "/api/v1/academic/students",
        json={
            "roll_number": "ECE999",
            "full_name": "Injected ECE Student",
            "institutional_email": "ece999@kucet.ac.in",
            "cohort_id": ece_cohort_id,
        },
    )
    assert cross_create.status_code == 403
    assert cross_create.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 4. Registering into CSE cohort succeeds
    valid_create = client.post(
        "/api/v1/academic/students",
        json={
            "roll_number": "CSE002",
            "full_name": "Valid CSE Student",
            "institutional_email": "cse002@kucet.ac.in",
            "cohort_id": cse_cohort_id,
        },
    )
    assert valid_create.status_code == 201


def test_developer_role_has_root_authority(db_session: Session, rbac_fixture: dict):
    """Developer possesses system-wide authority across all departments."""
    client = make_client(db_session, rbac_fixture["developer_user"])

    res = client.get("/api/v1/academic/departments")
    assert res.status_code == 200

    students_res = client.get("/api/v1/academic/students")
    assert students_res.status_code == 200
    rolls = [s["roll_number"] for s in students_res.json()["data"]]
    assert "CSE001" in rolls and "ECE001" in rolls


def test_unassigned_admin_fails_closed(db_session: Session, rbac_fixture: dict):
    """An ADMIN user with no assigned department_id must fail closed on all department operations."""
    unassigned_admin = User(
        id=str(uuid.uuid4()),
        email="unassigned.admin@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.ADMIN,
        department_id=None,
        is_active=True,
    )
    db_session.add(unassigned_admin)
    db_session.commit()

    client = make_client(db_session, unassigned_admin)

    # 1. Querying cohorts must fail closed
    res = client.get("/api/v1/academic/cohorts")
    assert res.status_code == 403
    assert res.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 2. Querying students must fail closed
    res_students = client.get("/api/v1/academic/students")
    assert res_students.status_code == 403
    assert res_students.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 3. Creating cohort must fail closed
    res_create = client.post(
        "/api/v1/academic/cohorts",
        json={
            "name": "TEST-2024-2028",
            "department_id": rbac_fixture["cse_dept"].id,
            "admission_year": 2024,
            "graduation_year": 2028,
        },
    )
    assert res_create.status_code == 403
    assert res_create.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"


def test_firebase_token_exchange_flow(db_session: Session, rbac_fixture: dict, monkeypatch):
    """Verifies exchanging a Firebase ID token for an institutional scoped JWT."""
    from unittest.mock import MagicMock
    import app.services.auth_service as auth_svc_mod

    mock_verify = MagicMock(return_value={
        "uid": "fb_uid_12345",
        "email": "hod.cse@kucet.ac.in",
    })
    monkeypatch.setattr(auth_svc_mod, "verify_firebase_id_token", mock_verify)

    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # Valid token exchange
    res = client.post("/api/v1/auth/firebase", json={"id_token": "valid_mock_firebase_token"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["email"] == "hod.cse@kucet.ac.in"
    assert data["role"] == "ADMIN"
    assert data["access_token"] is not None

    # Unknown user identity fails closed with 401
    mock_unknown = MagicMock(return_value={
        "uid": "fb_unknown_999",
        "email": "intruder@external.com",
    })
    monkeypatch.setattr(auth_svc_mod, "verify_firebase_id_token", mock_unknown)
    bad_res = client.post("/api/v1/auth/firebase", json={"id_token": "unknown_firebase_token"})
    assert bad_res.status_code == 401
    assert bad_res.json()["error"]["reason_code"] == "USER_NOT_REGISTERED"

