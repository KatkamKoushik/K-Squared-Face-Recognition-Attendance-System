"""
FRS V7.1 K² — Atomic Attendance Commit, Uniqueness & Idempotency Tests.
"""

import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.errors import IdempotencyConflictError
from app.domain.enums import SessionState, AttendanceStatus, UnitStatus
from app.domain.models.session import AttendanceSession, AttendanceUnit
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent
from app.schemas.attendance import AttendanceCommitRequest, StudentUnitDecision
from app.services.commit_service import CommitService


def test_atomic_commit_and_idempotency_receipt(db_session: Session, seed_data):
    """
    Invariants FR-08, FR-13:
    1. Atomic commit writes attendance rows, unit completion, audit event, and durable receipt.
    2. Replaying the identical idempotency key returns the original receipt without duplicating rows.
    """
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    students = seed_data["students"]

    # 1. Create a 2-unit session
    session = AttendanceSession(
        offering_id=seed_data["offering"].id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    u2 = AttendanceUnit(session_id=session.id, unit_index=2, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add_all([u1, u2])
    db_session.flush()

    # 2. Build decisions: 3 students across 2 units = 6 unit decisions
    decisions = [
        StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[1].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[2].id, unit_index=1, status=AttendanceStatus.ABSENT_CONFIRMED),
        StudentUnitDecision(student_id=students[0].id, unit_index=2, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[1].id, unit_index=2, status=AttendanceStatus.ABSENT_CONFIRMED),
        StudentUnitDecision(student_id=students[2].id, unit_index=2, status=AttendanceStatus.ABSENT_CONFIRMED),
    ]

    commit_req = AttendanceCommitRequest(
        idempotency_key="idemp_key_test_atomic_12345",
        conducted_unit_indices=[1, 2],
        decisions=decisions,
    )

    # 3. Execute first commit
    receipt1 = CommitService.commit_session_attendance(
        db=db_session,
        session_id=session.id,
        user_id=fac_user.id,
        faculty_id=faculty.id,
        request=commit_req,
        correlation_id="corr-test-01",
    )
    assert receipt1 is not None
    assert receipt1.total_conducted_units == 2
    assert receipt1.total_present_records == 3
    assert receipt1.total_absent_records == 3
    assert receipt1.receipt_hash is not None

    records_count = db_session.execute(select(func.count(AttendanceRecord.id))).scalar()
    assert records_count == 6
    assert session.state == SessionState.FINALIZED

    audit = db_session.execute(select(AuditEvent).where(AuditEvent.session_id == session.id)).scalar_one_or_none()
    assert audit is not None
    assert audit.actor_id == fac_user.id

    # 4. Idempotency Replay Test: re-executing with the same idempotency key
    receipt2 = CommitService.commit_session_attendance(
        db=db_session,
        session_id=session.id,
        user_id=fac_user.id,
        faculty_id=faculty.id,
        request=commit_req,
        correlation_id="corr-test-02",
    )
    assert receipt2.id == receipt1.id
    assert receipt2.receipt_hash == receipt1.receipt_hash

    records_count_after = db_session.execute(select(func.count(AttendanceRecord.id))).scalar()
    assert records_count_after == 6


def test_idempotency_conflict_on_mismatched_session(db_session: Session, seed_data):
    """Reusing the same idempotency key on a different session raises IdempotencyConflictError."""
    receipt = CommitReceipt(
        session_id="session_A",
        idempotency_key="idemp_key_reused_fail",
        committed_by_user_id=seed_data["faculty_user"].id,
        total_conducted_units=1,
        total_present_records=1,
        total_absent_records=0,
        receipt_hash="hash123",
    )
    db_session.add(receipt)
    db_session.flush()

    commit_req = AttendanceCommitRequest(
        idempotency_key="idemp_key_reused_fail",
        conducted_unit_indices=[1],
        decisions=[
            StudentUnitDecision(
                student_id=seed_data["students"][0].id,
                unit_index=1,
                status=AttendanceStatus.PRESENT_CONFIRMED,
            )
        ],
    )

    with pytest.raises(IdempotencyConflictError):
        CommitService.commit_session_attendance(
            db=db_session,
            session_id="session_B_different",
            user_id=seed_data["faculty_user"].id,
            faculty_id=seed_data["faculty"].id,
            request=commit_req,
            correlation_id="corr-99",
        )
