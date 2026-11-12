"""
FRS V7.1 K² — Cross-Faculty Object-Level Authorization (IDOR) & Commit Invariant Tests.
Verifies that faculty members cannot view, upload to, confirm, or commit another faculty's sessions.
"""

import io
import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import create_application
from app.core.database import get_db
from app.core.security import create_access_token
from app.domain.enums import SessionState, AttendanceStatus, UnitStatus
from app.domain.models.academic import User, Faculty, FacultyAssignment
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot, SnapshotStudentItem
from app.schemas.attendance import AttendanceCommitRequest, StudentUnitDecision
from app.services.commit_service import CommitService
from app.core.errors import PermissionDeniedError, StateTransitionError


def test_cross_faculty_idor_prevention(db_session: Session, seed_data):
    """
    Invariants FR-01, Section 11:
    Faculty B cannot access or modify Session owned by Faculty A.
    """
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    faculty_a = seed_data["faculty"]
    offering = seed_data["offering"]

    # Create Faculty B and User B
    user_b = User(email="faculty_b@kucet.ac.in", hashed_password="pw", role="FACULTY")
    db_session.add(user_b)
    db_session.flush()

    faculty_b = Faculty(user_id=user_b.id, employee_id="FAC-B-001", full_name="Faculty B", department_id=seed_data["department"].id)
    db_session.add(faculty_b)
    db_session.flush()

    # Create Session owned by Faculty A
    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty_a.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add(u1)
    db_session.flush()

    # Generate Bearer Token for Faculty B
    token_b = create_access_token(subject=str(user_b.id), role="FACULTY")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. GET /api/v1/sessions/{id} by Faculty B -> 403 Forbidden
    res = client.get(f"/api/v1/sessions/{session.id}", headers=headers_b)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 2. GET /api/v1/sessions/{id}/roster by Faculty B -> 403 Forbidden
    res = client.get(f"/api/v1/sessions/{session.id}/roster", headers=headers_b)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 3. POST /api/v1/sessions/{id}/units/1/confirm by Faculty B -> 403 Forbidden
    res = client.post(
        f"/api/v1/sessions/{session.id}/units/1/confirm",
        headers=headers_b,
        json={"unit_index": 1, "is_conducted": True},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 4. POST /api/v1/sessions/{id}/frames by Faculty B -> 403 Forbidden
    sample_img = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08")
    res = client.post(
        f"/api/v1/sessions/{session.id}/frames",
        headers=headers_b,
        files={"file": ("sweep.jpg", sample_img, "image/jpeg")},
        data={"frame_index": 0},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 5. GET /api/v1/sessions/{id}/proposal by Faculty B -> 403 Forbidden
    res = client.get(f"/api/v1/sessions/{session.id}/proposal", headers=headers_b)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "RESOURCE_FORBIDDEN"


def test_commit_invariants_and_roster_validation(db_session: Session, seed_data):
    """
    Verifies commit guards:
    - Non-IN_REVIEW session cannot be committed.
    - Out-of-roster student rejected.
    - Duplicate decision rejected.
    """
    faculty = seed_data["faculty"]
    user = seed_data["faculty_user"]
    students = seed_data["students"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.CAPTURING,  # Not IN_REVIEW
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add(u1)
    db_session.flush()

    # Attach roster snapshot with students[0] and students[1] only
    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=2)
    db_session.add(snapshot)
    db_session.flush()

    item1 = SnapshotStudentItem(snapshot_id=snapshot.id, student_id=students[0].id, roll_number=students[0].roll_number, full_name=students[0].full_name, cohort_id=students[0].cohort_id)
    item2 = SnapshotStudentItem(snapshot_id=snapshot.id, student_id=students[1].id, roll_number=students[1].roll_number, full_name=students[1].full_name, cohort_id=students[1].cohort_id)
    db_session.add_all([item1, item2])
    db_session.flush()

    # Attempt commit when session is in CAPTURING -> StateTransitionError
    commit_req = AttendanceCommitRequest(
        idempotency_key="idemp_state_err_001",
        conducted_unit_indices=[1],
        decisions=[
            StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        ],
    )

    with pytest.raises(StateTransitionError):
        CommitService.commit_session_attendance(
            db=db_session,
            session_id=session.id,
            user_id=user.id,
            faculty_id=faculty.id,
            request=commit_req,
            correlation_id="corr-err-1",
        )

    # Transition to IN_REVIEW
    session.state = SessionState.IN_REVIEW
    db_session.flush()

    # Out-of-roster student decision -> ValueError
    bad_req = AttendanceCommitRequest(
        idempotency_key="idemp_bad_student_002",
        conducted_unit_indices=[1],
        decisions=[
            StudentUnitDecision(student_id="unregistered_student_uuid", unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        ],
    )
    with pytest.raises(ValueError, match="not present in the frozen roster snapshot"):
        CommitService.commit_session_attendance(
            db=db_session,
            session_id=session.id,
            user_id=user.id,
            faculty_id=faculty.id,
            request=bad_req,
            correlation_id="corr-err-2",
        )

    # Duplicate decision tuple -> ValueError
    dup_req = AttendanceCommitRequest(
        idempotency_key="idemp_dup_student_003",
        conducted_unit_indices=[1],
        decisions=[
            StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
            StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.ABSENT_CONFIRMED),
        ],
    )
    with pytest.raises(ValueError, match="Duplicate attendance decision"):
        CommitService.commit_session_attendance(
            db=db_session,
            session_id=session.id,
            user_id=user.id,
            faculty_id=faculty.id,
            request=dup_req,
            correlation_id="corr-err-3",
        )


def test_offering_analytics_authorization(db_session: Session, seed_data):
    """
    P0.7: Verify object-level authorization on GET /api/v1/offerings/{id}/analytics.
    - Assigned faculty has access.
    - Unassigned faculty is forbidden (403).
    - Administrator has institutional scope (200).
    """
    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    offering = seed_data["offering"]
    user_a = seed_data["faculty_user"]
    token_a = create_access_token(subject=str(user_a.id), role="FACULTY")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Faculty B (unassigned)
    user_b = User(email="faculty_b_analytics@kucet.ac.in", hashed_password="pw", role="FACULTY")
    db_session.add(user_b)
    db_session.flush()

    faculty_b = Faculty(user_id=user_b.id, employee_id="FAC-B-002", full_name="Faculty B Analytics", department_id=seed_data["department"].id)
    db_session.add(faculty_b)
    db_session.flush()

    token_b = create_access_token(subject=str(user_b.id), role="FACULTY")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Admin (scoped to offering's department)
    admin_user = User(email="admin_analytics@kucet.ac.in", hashed_password="pw", role="ADMIN", department_id=seed_data["department"].id)
    db_session.add(admin_user)
    db_session.flush()
    token_admin = create_access_token(subject=str(admin_user.id), role="ADMIN")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 1. Unassigned faculty B -> 403 Forbidden
    res_b = client.get(f"/api/v1/offerings/{offering.id}/analytics", headers=headers_b)
    assert res_b.status_code == 403
    assert res_b.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 2. Assigned faculty A -> 200 OK
    res_a = client.get(f"/api/v1/offerings/{offering.id}/analytics", headers=headers_a)
    assert res_a.status_code == 200
    assert "data" in res_a.json()

    # 3. Administrator -> 200 OK
    res_admin = client.get(f"/api/v1/offerings/{offering.id}/analytics", headers=headers_admin)
    assert res_admin.status_code == 200
    assert "data" in res_admin.json()


def test_student_directory_scoped_authorization(db_session: Session, seed_data):
    """
    P0.7: Verify object-level authorization on GET /api/v1/academic/students.
    - Faculty cannot query students from unassigned cohorts (403).
    - Faculty can query students from assigned cohorts (200).
    - Admin has institutional access across any cohort (200).
    """
    from app.domain.models.academic import Cohort
    from app.domain.models.student import Student

    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    cohort_a = seed_data["cohort1"]
    cohort_b = seed_data["cohort2"]
    user_a = seed_data["faculty_user"]
    token_a = create_access_token(subject=str(user_a.id), role="FACULTY")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Add a student to unassigned cohort B
    student_b = Student(
        roll_number="23CSD01",
        full_name="CSD Student 1",
        cohort_id=cohort_b.id,
    )
    db_session.add(student_b)
    db_session.flush()

    # Admin
    admin_user = User(
        email="admin_students@kucet.ac.in",
        hashed_password="pw",
        role="ADMIN",
        department_id=seed_data["department"].id,
    )
    db_session.add(admin_user)
    db_session.flush()
    token_admin = create_access_token(subject=str(admin_user.id), role="ADMIN")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 1. Faculty A queries unassigned cohort B -> 403 Forbidden
    res_unassigned = client.get(f"/api/v1/academic/students?cohort_id={cohort_b.id}", headers=headers_a)
    assert res_unassigned.status_code == 403
    assert res_unassigned.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 2. Faculty A queries assigned cohort A -> 200 OK
    res_assigned = client.get(f"/api/v1/academic/students?cohort_id={cohort_a.id}", headers=headers_a)
    assert res_assigned.status_code == 200
    assert len(res_assigned.json()["data"]) >= 1

    # 3. Admin queries unassigned cohort B -> 200 OK
    res_admin = client.get(f"/api/v1/academic/students?cohort_id={cohort_b.id}", headers=headers_admin)
    assert res_admin.status_code == 200
    assert len(res_admin.json()["data"]) == 1


def test_commit_receipt_retrieval_authorization(db_session: Session, seed_data):
    """
    P0.4: Verify object-level authorization on GET /api/v1/sessions/{id}/receipt.
    - Non-owner faculty is forbidden (403).
    - Session owner has access (200).
    - Admin has access (200).
    """
    from app.domain.models.audit import CommitReceipt

    app = create_application()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    faculty_a = seed_data["faculty"]
    user_a = seed_data["faculty_user"]
    token_a = create_access_token(subject=str(user_a.id), role="FACULTY")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    offering = seed_data["offering"]
    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty_a.id,
        state=SessionState.FINALIZED,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    receipt = CommitReceipt(
        session_id=session.id,
        idempotency_key="idemp_receipt_test_001",
        committed_by_user_id=user_a.id,
        total_conducted_units=1,
        total_present_records=1,
        total_absent_records=0,
        receipt_hash="0xabcd1234deadbeef",
    )
    db_session.add(receipt)
    db_session.flush()

    # Faculty B (not owner)
    user_b = User(email="faculty_b_receipt@kucet.ac.in", hashed_password="pw", role="FACULTY")
    db_session.add(user_b)
    db_session.flush()
    faculty_b = Faculty(user_id=user_b.id, employee_id="FAC-B-003", full_name="Faculty B Receipt", department_id=seed_data["department"].id)
    db_session.add(faculty_b)
    db_session.flush()
    token_b = create_access_token(subject=str(user_b.id), role="FACULTY")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Admin
    admin_user = User(email="admin_receipt@kucet.ac.in", hashed_password="pw", role="ADMIN")
    db_session.add(admin_user)
    db_session.flush()
    token_admin = create_access_token(subject=str(admin_user.id), role="ADMIN")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 1. Faculty B -> 403 Forbidden
    res_b = client.get(f"/api/v1/sessions/{session.id}/receipt", headers=headers_b)
    assert res_b.status_code == 403
    assert res_b.json()["error"]["code"] == "RESOURCE_FORBIDDEN"

    # 2. Faculty A (owner) -> 200 OK
    res_a = client.get(f"/api/v1/sessions/{session.id}/receipt", headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["data"]["receipt_hash"] == "0xabcd1234deadbeef"

    # 3. Admin -> 200 OK
    res_admin = client.get(f"/api/v1/sessions/{session.id}/receipt", headers=headers_admin)
    assert res_admin.status_code == 200
    assert res_admin.json()["data"]["receipt_hash"] == "0xabcd1234deadbeef"
