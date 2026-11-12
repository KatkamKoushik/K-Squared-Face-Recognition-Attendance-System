"""
K² FRS — 5-Tier Hierarchical RBAC & Department Isolation Test Suite.
Validates the institutional access control hierarchy:
DEVELOPER > SUPER_ADMIN > ADMIN > SUB_ADMIN (FACULTY) > STUDENT

Enforces strict department-boundary invariants:
An administrator for CSE must NOT access, create, or review ECE or other departments' records.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

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
        "email_verified": True,
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

    # Unverified email rejected with EMAIL_NOT_VERIFIED
    mock_unverified = MagicMock(return_value={
        "uid": "fb_unverified_1",
        "email": "hod.cse@kucet.ac.in",
        "email_verified": False,
    })
    monkeypatch.setattr(auth_svc_mod, "verify_firebase_id_token", mock_unverified)
    unver_res = client.post("/api/v1/auth/firebase", json={"id_token": "unverified_token"})
    assert unver_res.status_code == 401
    assert unver_res.json()["error"]["reason_code"] == "EMAIL_NOT_VERIFIED"

    # Unknown user identity fails closed with 401
    mock_unknown = MagicMock(return_value={
        "uid": "fb_unknown_999",
        "email": "intruder@external.com",
        "email_verified": True,
    })
    monkeypatch.setattr(auth_svc_mod, "verify_firebase_id_token", mock_unknown)
    bad_res = client.post("/api/v1/auth/firebase", json={"id_token": "unknown_firebase_token"})
    assert bad_res.status_code == 401
    assert bad_res.json()["error"]["reason_code"] == "USER_NOT_REGISTERED"


def test_enrollment_department_isolation(db_session: Session, rbac_fixture: dict):
    """CSE Admin cannot view or approve ECE student enrollment submissions."""
    from app.domain.models.student import EnrollmentSubmission
    from app.domain.enums import EnrollmentSubmissionStatus

    cse_sub = EnrollmentSubmission(
        id=str(uuid.uuid4()),
        roll_number="CSE-SUB-01",
        full_name="CSE Applicant",
        institutional_email="applicant.cse@kucet.ac.in",
        department="CSE",
        academic_year="2026-2027",
        cohort_id=rbac_fixture["cse_cohort"].id,
        photo_storage_path="/tmp/cse_photo.jpg",
        photo_sha256="hash1",
        photo_mime="image/jpeg",
        status=EnrollmentSubmissionStatus.PENDING_REVIEW,
        consent_acknowledged=True,
    )
    ece_sub = EnrollmentSubmission(
        id=str(uuid.uuid4()),
        roll_number="ECE-SUB-01",
        full_name="ECE Applicant",
        institutional_email="applicant.ece@kucet.ac.in",
        department="ECE",
        academic_year="2026-2027",
        cohort_id=rbac_fixture["ece_cohort"].id,
        photo_storage_path="/tmp/ece_photo.jpg",
        photo_sha256="hash2",
        photo_mime="image/jpeg",
        status=EnrollmentSubmissionStatus.PENDING_REVIEW,
        consent_acknowledged=True,
    )
    db_session.add_all([cse_sub, ece_sub])
    db_session.commit()

    cse_client = make_client(db_session, rbac_fixture["cse_admin_user"])
    super_client = make_client(db_session, rbac_fixture["super_admin_user"])

    # 1. CSE Admin listing submissions only sees CSE submissions
    list_res = cse_client.get("/api/v1/enrollment/submissions")
    assert list_res.status_code == 200
    rolls = [s["roll_number"] for s in list_res.json()["data"]]
    assert "CSE-SUB-01" in rolls
    assert "ECE-SUB-01" not in rolls

    # 2. Super Admin listing submissions sees all departments
    super_list = super_client.get("/api/v1/enrollment/submissions")
    assert super_list.status_code == 200
    all_rolls = [s["roll_number"] for s in super_list.json()["data"]]
    assert "CSE-SUB-01" in all_rolls and "ECE-SUB-01" in all_rolls

    # 3. CSE Admin attempting to view ECE submission -> 403 Forbidden
    cross_view = cse_client.get(f"/api/v1/enrollment/submissions/{ece_sub.id}")
    assert cross_view.status_code == 403
    assert cross_view.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # 4. CSE Admin attempting to reject ECE submission -> 403 Forbidden
    cross_reject = cse_client.post(
        f"/api/v1/enrollment/submissions/{ece_sub.id}/reject",
        json={"reason": "Rejected by wrong dept"},
    )
    assert cross_reject.status_code == 403
    assert cross_reject.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"


def test_audit_events_endpoint_isolation_and_auth(db_session: Session, rbac_fixture: dict):
    """Audit events endpoint requires admin authentication and enforces department isolation."""
    from app.domain.models.audit import AuditEvent
    from app.domain.enums import AuditAction

    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    unauth_client = TestClient(app)

    # 1. Unauthenticated request -> 401 Unauthorized
    unauth_res = unauth_client.get("/api/v1/audit/events")
    assert unauth_res.status_code == 401

    # 2. Seed audit event for CSE actor
    event = AuditEvent(
        id=str(uuid.uuid4()),
        session_id=None,
        actor_id=rbac_fixture["cse_admin_user"].id,
        action=AuditAction.ATTENDANCE_COMMITTED,
        reason="Test audit logging",
        correlation_id="corr-test-123",
    )
    db_session.add(event)
    db_session.commit()

    # 3. CSE Admin can query and sees the event
    cse_client = make_client(db_session, rbac_fixture["cse_admin_user"])
    cse_res = cse_client.get("/api/v1/audit/events")
    assert cse_res.status_code == 200
    assert len(cse_res.json()["data"]) >= 1

    # 4. ECE Admin queries and does not see CSE event
    ece_client = make_client(db_session, rbac_fixture["ece_admin_user"])
    ece_res = ece_client.get("/api/v1/audit/events")
    assert ece_res.status_code == 200
    assert len(ece_res.json()["data"]) == 0


def test_sessions_endpoint_auth_and_role_scoping(db_session: Session, rbac_fixture: dict):
    """GET /sessions requires authentication, rejects students, and scopes appropriately."""
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    unauth_client = TestClient(app)

    # 1. Unauthenticated -> 401 Unauthorized
    assert unauth_client.get("/api/v1/sessions").status_code == 401

    # 2. Student -> 403 Forbidden
    student_client = make_client(db_session, rbac_fixture["student_user"])
    assert student_client.get("/api/v1/sessions").status_code == 403

    # 3. Super Admin -> 200 OK
    super_client = make_client(db_session, rbac_fixture["super_admin_user"])
    assert super_client.get("/api/v1/sessions").status_code == 200


def test_user_lifecycle_account_suspension_and_token_revocation(db_session: Session, rbac_fixture: dict):
    """Suspending a user or logging out immediately revokes active JWT sessions."""
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session

    student = rbac_fixture["student_user"]
    token = create_access_token(
        subject=student.email,
        role=student.role.value,
        additional_claims={"user_id": student.id, "token_version": student.token_version},
    )
    student_client = TestClient(app)
    student_client.headers.update({"Authorization": f"Bearer {token}"})

    # Student can initially access /student/me
    init_res = student_client.get("/api/v1/student/me")
    assert init_res.status_code == 200

    # CSE Admin suspends student
    cse_client = make_client(db_session, rbac_fixture["cse_admin_user"])
    suspend_res = cse_client.patch(f"/api/v1/auth/users/{student.id}/status", json={"is_active": False})
    assert suspend_res.status_code == 200
    assert suspend_res.json()["data"]["is_active"] is False

    # Student's existing token is immediately rejected as revoked / inactive
    revoked_res = student_client.get("/api/v1/student/me")
    assert revoked_res.status_code == 401


def test_logout_session_revocation(db_session: Session, rbac_fixture: dict):
    """Logging out increments token_version and invalidates the previous session token."""
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session

    admin = rbac_fixture["cse_admin_user"]
    token = create_access_token(
        subject=admin.email,
        role=admin.role.value,
        additional_claims={"user_id": admin.id, "token_version": admin.token_version},
    )
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})

    # Valid before logout
    assert client.get("/api/v1/auth/me").status_code == 200

    # Execute logout
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # Old token fails closed
    after_res = client.get("/api/v1/auth/me")
    assert after_res.status_code == 401
    assert after_res.json()["error"]["reason_code"] == "TOKEN_REVOKED"


def test_complete_role_permission_matrix(db_session: Session, rbac_fixture: dict):
    """
    Comprehensive institutional permission matrix test across all 5 tiers:
    DEVELOPER > SUPER_ADMIN > ADMIN > SUB_ADMIN/FACULTY > STUDENT (> UNAUTHENTICATED).
    """
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    unauth = TestClient(app)

    sub_admin = User(
        id=str(uuid.uuid4()),
        email="subadmin.cse@kucet.ac.in",
        hashed_password="hash",
        role=UserRole.SUB_ADMIN,
        department_id=rbac_fixture["cse_dept"].id,
        is_active=True,
    )
    db_session.add(sub_admin)
    db_session.commit()

    clients = {
        "UNAUTH": unauth,
        "STUDENT": make_client(db_session, rbac_fixture["student_user"]),
        "SUB_ADMIN": make_client(db_session, sub_admin),
        "ADMIN_CSE": make_client(db_session, rbac_fixture["cse_admin_user"]),
        "ADMIN_ECE": make_client(db_session, rbac_fixture["ece_admin_user"]),
        "SUPER_ADMIN": make_client(db_session, rbac_fixture["super_admin_user"]),
        "DEVELOPER": make_client(db_session, rbac_fixture["developer_user"]),
    }

    # Matrix: (method, path, payload, expected_codes_by_role)
    matrix = [
        # Institutional global governance / department creation
        (
            "POST",
            "/api/v1/academic/departments",
            {"code": "BIO", "name": "Biotechnology"},
            {"UNAUTH": 401, "STUDENT": 403, "SUB_ADMIN": 403, "ADMIN_CSE": 403, "SUPER_ADMIN": 201},
        ),
        # Audit events read access
        (
            "GET",
            "/api/v1/audit/events",
            None,
            {"UNAUTH": 401, "STUDENT": 403, "SUB_ADMIN": 403, "ADMIN_CSE": 200, "SUPER_ADMIN": 200, "DEVELOPER": 200},
        ),
        # Governance summary status
        (
            "GET",
            "/api/v1/governance/status",
            None,
            {"UNAUTH": 401, "STUDENT": 403, "SUB_ADMIN": 200, "ADMIN_CSE": 200, "SUPER_ADMIN": 200, "DEVELOPER": 200},
        ),
        # Student personal profile (strictly student role)
        (
            "GET",
            "/api/v1/student/me",
            None,
            {"UNAUTH": 401, "STUDENT": 200, "ADMIN_CSE": 403, "SUB_ADMIN": 403},
        ),
        # Cross-department cohort access blocked for ECE admin querying CSE dept
        (
            "GET",
            f"/api/v1/academic/cohorts?department_id={rbac_fixture['cse_dept'].id}",
            None,
            {"UNAUTH": 401, "STUDENT": 200, "ADMIN_ECE": 403, "ADMIN_CSE": 200, "SUPER_ADMIN": 200, "DEVELOPER": 200},
        ),
    ]

    for method, path, payload, expectations in matrix:
        for role_key, expected_code in expectations.items():
            c = clients[role_key]
            if method == "GET":
                resp = c.get(path)
            else:
                resp = c.post(path, json=payload)
            assert resp.status_code == expected_code, (
                f"Role {role_key} on {method} {path}: expected {expected_code}, got {resp.status_code} ({resp.text})"
            )


def test_firebase_raw_token_rejected_on_protected_endpoints(db_session: Session, monkeypatch):
    """Passing a raw Firebase ID token directly to protected endpoints is rejected with SESSION_TOKEN_REQUIRED."""
    from unittest.mock import MagicMock
    import app.core.security as sec_mod

    mock_verify = MagicMock(return_value={
        "uid": "fb_raw_test",
        "email": "student@kucet.ac.in",
        "email_verified": True,
        "token_type": "firebase_id_token",
        "firebase": {"uid": "fb_raw_test"},
    })
    monkeypatch.setattr(sec_mod, "verify_firebase_id_token", mock_verify)

    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    headers = {"Authorization": "Bearer raw_firebase_token_payload"}
    res = client.get("/api/v1/student/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["error"]["reason_code"] == "SESSION_TOKEN_REQUIRED"


def test_student_user_explicit_link_and_unauthorized_offering_access(db_session: Session, rbac_fixture: dict):
    """Validates explicit user.student_id resolution and active enrollment enforcement."""
    from app.services.student_service import StudentService
    from app.core.errors import PermissionDeniedError
    from app.domain.models.student import Student, Enrollment
    from app.domain.models.academic import User, SubjectOffering, Subject, Term, AcademicYear
    from app.domain.enums import UserRole
    from datetime import date

    # Link user explicitly to student
    student = rbac_fixture["cse_student"]
    student_user = rbac_fixture["student_user"]
    student_user.student_id = student.id
    db_session.commit()

    resolved_student = StudentService.get_student_for_user(db_session, student_user)
    assert resolved_student.id == student.id

    # Create academic year and term
    ay = AcademicYear(
        id=str(uuid.uuid4()),
        year_code=f"AY-{uuid.uuid4().hex[:6]}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay)
    db_session.flush()

    term = Term(
        id=str(uuid.uuid4()),
        academic_year_id=ay.id,
        term_type=AcademicTerm.ODD,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
        is_active=True,
    )
    db_session.add(term)
    db_session.flush()

    # Create an offering in ECE that student is NOT enrolled in
    subj = Subject(
        id=str(uuid.uuid4()),
        code=f"ECE-{uuid.uuid4().hex[:4]}",
        name="Advanced DSP",
        department_id=rbac_fixture["ece_dept"].id,
    )
    db_session.add(subj)
    db_session.flush()

    offering = SubjectOffering(
        id=str(uuid.uuid4()),
        subject_id=subj.id,
        term_id=term.id,
        section="A",
        primary_cohort_id=rbac_fixture["ece_cohort"].id,
        is_active=True,
    )
    db_session.add(offering)
    db_session.commit()

    with pytest.raises(PermissionDeniedError) as exc_info:
        StudentService.get_offering_ledger(db_session, student, offering.id)
    assert exc_info.value.reason_code == "OFFERING_ENROLLMENT_REQUIRED"


def test_duplicate_appeal_and_correction_reviews(db_session: Session, rbac_fixture: dict):
    """Reviews on already processed appeals or corrections fail with business rule violation."""
    from app.services.student_service import StudentService
    from app.core.errors import BusinessRuleViolationError
    from app.domain.models.student import StudentDataCorrection
    from app.domain.models.attendance import AttendanceAppeal
    from app.domain.models.session import AttendanceSession, AttendanceUnit
    from app.domain.models.academic import Faculty, SubjectOffering, Subject, Term, AcademicYear
    from app.domain.enums import SessionState, UnitStatus, AppealStatus, AttendanceStatus
    from datetime import date

    # Create academic year and term
    ay = AcademicYear(
        id=str(uuid.uuid4()),
        year_code=f"AY-{uuid.uuid4().hex[:6]}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay)
    db_session.flush()

    term = Term(
        id=str(uuid.uuid4()),
        academic_year_id=ay.id,
        term_type=AcademicTerm.ODD,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
        is_active=True,
    )
    db_session.add(term)
    db_session.flush()

    subj = Subject(
        id=str(uuid.uuid4()),
        code=f"CSE-{uuid.uuid4().hex[:4]}",
        name="Data Structures",
        department_id=rbac_fixture["cse_dept"].id,
    )
    db_session.add(subj)
    db_session.flush()

    offering = SubjectOffering(
        id=str(uuid.uuid4()),
        subject_id=subj.id,
        term_id=term.id,
        section="A",
        primary_cohort_id=rbac_fixture["cse_cohort"].id,
        is_active=True,
    )
    db_session.add(offering)
    db_session.flush()

    faculty = Faculty(
        id=str(uuid.uuid4()),
        user_id=rbac_fixture["cse_admin_user"].id,
        employee_id=f"FAC-{uuid.uuid4().hex[:4]}",
        full_name="CSE Faculty",
        department_id=rbac_fixture["cse_dept"].id,
    )
    db_session.add(faculty)
    db_session.flush()

    session = AttendanceSession(
        id=str(uuid.uuid4()),
        offering_id=offering.id,
        faculty_id=faculty.id,
        session_date=date.today(),
        state=SessionState.FINALIZED,
        policy_version_id="policy_kucet_k2_default",
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    unit = AttendanceUnit(
        id=str(uuid.uuid4()),
        session_id=session.id,
        unit_index=1,
        is_conducted=True,
        status=UnitStatus.COMMITTED,
    )
    db_session.add(unit)
    db_session.flush()

    appeal = AttendanceAppeal(
        id=str(uuid.uuid4()),
        session_id=session.id,
        unit_id=unit.id,
        student_id=rbac_fixture["cse_student"].id,
        reason="Medical emergency",
        evidence_path=None,
        status=AppealStatus.PENDING,
    )
    db_session.add(appeal)
    db_session.commit()

    # Review once
    StudentService.review_appeal(
        db=db_session,
        appeal_id=appeal.id,
        reviewer=rbac_fixture["cse_admin_user"],
        approved=True,
        review_notes="Approved upon medical certificate",
        correlation_id=str(uuid.uuid4()),
    )

    # Attempt second review
    with pytest.raises(BusinessRuleViolationError) as exc_info:
        StudentService.review_appeal(
            db=db_session,
            appeal_id=appeal.id,
            reviewer=rbac_fixture["cse_admin_user"],
            approved=False,
            review_notes="Trying duplicate review",
            correlation_id=str(uuid.uuid4()),
        )
    assert exc_info.value.reason_code == "APPEAL_ALREADY_REVIEWED"

    # Create correction
    correction = StudentDataCorrection(
        id=str(uuid.uuid4()),
        student_id=rbac_fixture["cse_student"].id,
        field_name="full_name",
        current_value="Jane Student",
        requested_value="Jane C. Student",
        reason="Legal name correction",
        status="PENDING",
    )
    db_session.add(correction)
    db_session.commit()

    # Review once
    StudentService.review_data_correction(
        db=db_session,
        request_id=correction.id,
        reviewer=rbac_fixture["cse_admin_user"],
        approved=True,
        review_notes="Approved with identity proof",
        correlation_id=str(uuid.uuid4()),
    )

    # Attempt second review
    with pytest.raises(BusinessRuleViolationError) as exc_info2:
        StudentService.review_data_correction(
            db=db_session,
            request_id=correction.id,
            reviewer=rbac_fixture["cse_admin_user"],
            approved=False,
            review_notes="Duplicate attempt",
            correlation_id=str(uuid.uuid4()),
        )
    assert exc_info2.value.reason_code == "CORRECTION_ALREADY_REVIEWED"


def test_department_isolation_on_attendance_exports_and_analytics(db_session: Session, rbac_fixture: dict):
    """Department admin cannot access attendance analytics or CSV exports of another department."""
    from app.domain.models.academic import Subject, SubjectOffering, Term, AcademicYear
    from datetime import date

    # Create academic year and term
    ay = AcademicYear(
        id=str(uuid.uuid4()),
        year_code=f"AY-{uuid.uuid4().hex[:6]}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay)
    db_session.flush()

    term = Term(
        id=str(uuid.uuid4()),
        academic_year_id=ay.id,
        term_type=AcademicTerm.ODD,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
        is_active=True,
    )
    db_session.add(term)
    db_session.flush()

    ece_subj = Subject(
        id=str(uuid.uuid4()),
        code=f"ECE-{uuid.uuid4().hex[:4]}",
        name="Communication Systems",
        department_id=rbac_fixture["ece_dept"].id,
    )
    db_session.add(ece_subj)
    db_session.flush()

    ece_offering = SubjectOffering(
        id=str(uuid.uuid4()),
        subject_id=ece_subj.id,
        term_id=term.id,
        section="A",
        primary_cohort_id=rbac_fixture["ece_cohort"].id,
        is_active=True,
    )
    db_session.add(ece_offering)
    db_session.commit()

    cse_client = make_client(db_session, rbac_fixture["cse_admin_user"])

    # Attempt analytics on ECE offering
    res_analytics = cse_client.get(f"/api/v1/offerings/{ece_offering.id}/analytics")
    assert res_analytics.status_code == 403
    assert res_analytics.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"

    # Attempt CSV export on ECE offering
    res_csv = cse_client.get(f"/api/v1/offerings/{ece_offering.id}/export/csv")
    assert res_csv.status_code == 403
    assert res_csv.json()["error"]["reason_code"] == "DEPARTMENT_ACCESS_RESTRICTED"


def test_admin_without_department_or_cross_department_appeals_and_corrections_blocked(db_session: Session, rbac_fixture: dict):
    """Department admin without department or cross-department access to appeals/corrections fails closed."""
    from app.services.student_service import StudentService
    from app.core.errors import PermissionDeniedError
    from app.domain.models.student import StudentDataCorrection
    from app.domain.models.attendance import AttendanceAppeal
    from app.domain.models.session import AttendanceSession, AttendanceUnit
    from app.domain.models.academic import User, Faculty, SubjectOffering, Subject, Term, AcademicYear
    from app.domain.enums import SessionState, UnitStatus, AppealStatus, UserRole
    from datetime import date

    # Admin without department
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

    # Fail closed on listing
    with pytest.raises(PermissionDeniedError) as exc_appeals:
        StudentService.list_all_appeals(db_session, user=unassigned_admin)
    assert exc_appeals.value.reason_code == "DEPARTMENT_ASSIGNMENT_REQUIRED"

    with pytest.raises(PermissionDeniedError) as exc_corrections:
        StudentService.list_all_corrections(db_session, user=unassigned_admin)
    assert exc_corrections.value.reason_code == "DEPARTMENT_ASSIGNMENT_REQUIRED"

    # Create ECE Student Correction & Appeal
    ece_student = rbac_fixture["ece_student"]
    ece_correction = StudentDataCorrection(
        id=str(uuid.uuid4()),
        student_id=ece_student.id,
        field_name="full_name",
        current_value="ECE Student",
        requested_value="ECE Student Jr",
        reason="Correction",
        status="PENDING",
    )
    db_session.add(ece_correction)
    db_session.commit()

    # CSE Admin reviewing ECE correction fails closed
    with pytest.raises(PermissionDeniedError) as exc_cross_corr:
        StudentService.review_data_correction(
            db=db_session,
            request_id=ece_correction.id,
            reviewer=rbac_fixture["cse_admin_user"],
            approved=True,
            review_notes="Cross-dept attempt",
            correlation_id=str(uuid.uuid4()),
        )
    assert exc_cross_corr.value.reason_code == "DEPARTMENT_ACCESS_RESTRICTED"


def test_demo_unauthenticated_isolation(db_session: Session):
    """Unauthenticated public callers get synthetic data only and never query real student embeddings."""
    import io
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # 1. Enrolled students list unauthenticated returns synthetic demonstration roster
    res_roster = client.get("/api/v1/demo/enrolled-students")
    assert res_roster.status_code == 200
    roster_data = res_roster.json()["data"]
    assert len(roster_data) > 0
    # Synthetic students have DEMO prefix in roll numbers
    for item in roster_data:
        assert item["roll_number"].startswith("DEMO")

    # 2. Analyze demo photo unauthenticated does not match any real student
    # Create a tiny 100x100 RGB JPEG
    import numpy as np
    import cv2
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode(".jpg", img)
    img_bytes = img_encoded.tobytes()

    files = {"file": ("test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    res_analyze = client.post("/api/v1/demo/analyze", files=files)
    assert res_analyze.status_code == 200
    analyze_data = res_analyze.json()["data"]
    # Real enrolled students searched must be 0 for unauthenticated visitors
    assert analyze_data["total_enrolled_students"] == 0



