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
