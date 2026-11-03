"""
FRS V7.1 K² — Phase P3 Attendance Ledger Completeness, Decision Matrix & Audited Corrections Tests.
Verifies complete Cartesian product validation, immutable audit trails for post-commit overrides/appeals,
and dynamic institutional analytics reconciliation.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import PermissionDeniedError, StateTransitionError, ResourceNotFoundError
from app.domain.enums import SessionState, AttendanceStatus, UnitStatus, AuditAction, UserRole
from app.domain.models.academic import User, Faculty
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot, SnapshotStudentItem
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent
from app.schemas.attendance import (
    AttendanceCommitRequest,
    StudentUnitDecision,
    AttendanceCorrectionRequest,
)
from app.services.commit_service import CommitService
from app.services.analytics_service import AnalyticsService


def test_decision_matrix_completeness_enforcement(db_session: Session, seed_data):
    """
    Phase P3: Every eligible student in the frozen roster snapshot must have an explicit
    decision for every conducted unit. Missing matrix cells fail closed.
    """
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    students = seed_data["students"]  # 3 students
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
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

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=len(students))
    db_session.add(snapshot)
    db_session.flush()

    for s in students:
        item = SnapshotStudentItem(
            snapshot_id=snapshot.id,
            student_id=s.id,
            roll_number=s.roll_number,
            full_name=s.full_name,
            cohort_id=s.cohort_id,
        )
        db_session.add(item)
    db_session.flush()

    # Cartesian product: 3 students x 2 units = 6 required decisions
    # Test 1: Partial decisions (omitting student 2 for unit 2) -> Fail Closed
    incomplete_decisions = [
        StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[1].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[2].id, unit_index=1, status=AttendanceStatus.ABSENT_CONFIRMED),
        StudentUnitDecision(student_id=students[0].id, unit_index=2, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[1].id, unit_index=2, status=AttendanceStatus.ABSENT_CONFIRMED),
        # Missing (students[2].id, unit 2)
    ]

    bad_commit_req = AttendanceCommitRequest(
        idempotency_key="idemp_incomplete_matrix_01",
        conducted_unit_indices=[1, 2],
        decisions=incomplete_decisions,
    )

    with pytest.raises(ValueError, match="Incomplete attendance decision matrix"):
        CommitService.commit_session_attendance(
            db=db_session,
            session_id=session.id,
            user_id=fac_user.id,
            faculty_id=faculty.id,
            request=bad_commit_req,
            correlation_id="corr-incomplete-01",
        )

    # Test 2: Full Cartesian product (all 6 decisions) -> Succeeds
    complete_decisions = incomplete_decisions + [
        StudentUnitDecision(student_id=students[2].id, unit_index=2, status=AttendanceStatus.ABSENT_CONFIRMED),
    ]

    good_commit_req = AttendanceCommitRequest(
        idempotency_key="idemp_complete_matrix_02",
        conducted_unit_indices=[1, 2],
        decisions=complete_decisions,
    )

    receipt = CommitService.commit_session_attendance(
        db=db_session,
        session_id=session.id,
        user_id=fac_user.id,
        faculty_id=faculty.id,
        request=good_commit_req,
        correlation_id="corr-complete-02",
    )

    assert receipt is not None
    assert receipt.total_conducted_units == 2
    assert receipt.total_present_records == 3
    assert receipt.total_absent_records == 3
    assert session.state == SessionState.FINALIZED


def test_post_commit_overrides_and_student_appeals(db_session: Session, seed_data):
    """
    Phase P3: Verifies audited post-commit adjustments:
    1. Faculty OVERRIDE from ABSENT to PRESENT.
    2. Admin APPEAL from ABSENT to EXCUSED with medical reference.
    3. Reconciled CommitReceipt and append-only AuditEvent logs.
    4. Immediate reflection in institutional AnalyticsService.
    """
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    admin_user = seed_data["admin_user"]
    students = seed_data["students"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add(u1)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=len(students))
    db_session.add(snapshot)
    db_session.flush()

    for s in students:
        item = SnapshotStudentItem(
            snapshot_id=snapshot.id,
            student_id=s.id,
            roll_number=s.roll_number,
            full_name=s.full_name,
            cohort_id=s.cohort_id,
        )
        db_session.add(item)
    db_session.flush()

    # Commit initial attendance: Student 0 present, Student 1 absent, Student 2 absent
    initial_decisions = [
        StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[1].id, unit_index=1, status=AttendanceStatus.ABSENT_CONFIRMED),
        StudentUnitDecision(student_id=students[2].id, unit_index=1, status=AttendanceStatus.ABSENT_CONFIRMED),
    ]

    receipt = CommitService.commit_session_attendance(
        db=db_session,
        session_id=session.id,
        user_id=fac_user.id,
        faculty_id=faculty.id,
        request=AttendanceCommitRequest(
            idempotency_key="idemp_post_commit_test_01",
            conducted_unit_indices=[1],
            decisions=initial_decisions,
        ),
        correlation_id="corr-init-01",
    )
    assert receipt.total_present_records == 1
    assert receipt.total_absent_records == 2

    # Check analytics before override: Student 1 has 0% attendance
    analytics_before = AnalyticsService.get_offering_attendance_analytics(db=db_session, offering_id=offering.id)
    stats_map_before = {s.student_id: s for s in analytics_before.student_stats}
    assert stats_map_before[students[1].id].attended_conducted_units == 0
    assert stats_map_before[students[1].id].attendance_percent == 0.0

    # Action 1: Faculty applies OVERRIDE for Student 1 (Absent -> Present)
    override_req = AttendanceCorrectionRequest(
        student_id=students[1].id,
        unit_index=1,
        new_status=AttendanceStatus.PRESENT_CONFIRMED,
        action_type="OVERRIDE",
        reason="Faculty verified student attendance slip signed in class.",
        reference_document=None,
    )

    override_resp = CommitService.apply_attendance_correction(
        db=db_session,
        session_id=session.id,
        user=fac_user,
        request=override_req,
        correlation_id="corr-override-01",
    )

    assert override_resp.previous_status == AttendanceStatus.ABSENT_CONFIRMED
    assert override_resp.new_status == AttendanceStatus.PRESENT_CONFIRMED
    assert override_resp.action == AuditAction.POST_COMMIT_OVERRIDE.value

    # Verify receipt counts updated
    updated_receipt = db_session.get(CommitReceipt, receipt.id)
    assert updated_receipt.total_present_records == 2
    assert updated_receipt.total_absent_records == 1

    # Verify AuditEvent recorded
    audit_override = db_session.execute(
        select(AuditEvent).where(AuditEvent.id == override_resp.audit_event_id)
    ).scalar_one()
    assert audit_override.action == AuditAction.POST_COMMIT_OVERRIDE
    assert audit_override.actor_id == fac_user.id
    assert audit_override.before_state["status"] == AttendanceStatus.ABSENT_CONFIRMED.value
    assert audit_override.after_state["status"] == AttendanceStatus.PRESENT_CONFIRMED.value

    # Action 2: Administrator processes student APPEAL for Student 2 (Absent -> Excused)
    appeal_req = AttendanceCorrectionRequest(
        student_id=students[2].id,
        unit_index=1,
        new_status=AttendanceStatus.EXCUSED,
        action_type="APPEAL",
        reason="Approved official medical leave endorsed by Department HOD.",
        reference_document="MED-CERT-2026-KU-009",
    )

    appeal_resp = CommitService.apply_attendance_correction(
        db=db_session,
        session_id=session.id,
        user=admin_user,
        request=appeal_req,
        correlation_id="corr-appeal-01",
    )

    assert appeal_resp.previous_status == AttendanceStatus.ABSENT_CONFIRMED
    assert appeal_resp.new_status == AttendanceStatus.EXCUSED
    assert appeal_resp.action == AuditAction.APPEAL_PROCESSED.value

    # Verify analytics after corrections: Student 1 now has 1/1 (100.0%)
    analytics_after = AnalyticsService.get_offering_attendance_analytics(db=db_session, offering_id=offering.id)
    stats_map_after = {s.student_id: s for s in analytics_after.student_stats}
    assert stats_map_after[students[1].id].attended_conducted_units == 1
    assert stats_map_after[students[1].id].attendance_percent == 100.0


def test_correction_authorization_and_invariants(db_session: Session, seed_data):
    """Verifies security & validation guards on attendance corrections."""
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    students = seed_data["students"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,  # Not FINALIZED
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add(u1)
    db_session.flush()

    correction_req = AttendanceCorrectionRequest(
        student_id=students[0].id,
        unit_index=1,
        new_status=AttendanceStatus.PRESENT_CONFIRMED,
        action_type="OVERRIDE",
        reason="Testing unfinalized session guardrail.",
    )

    # 1. State Guard: Cannot correct unfinalized session
    with pytest.raises(StateTransitionError):
        CommitService.apply_attendance_correction(
            db=db_session,
            session_id=session.id,
            user=fac_user,
            request=correction_req,
            correlation_id="corr-inv-01",
        )

    # Finalize session and add an attendance record
    session.state = SessionState.FINALIZED
    u1.status = UnitStatus.COMMITTED
    rec = AttendanceRecord(
        session_id=session.id,
        unit_id=u1.id,
        student_id=students[0].id,
        status=AttendanceStatus.PRESENT_CONFIRMED,
        finalized_by_user_id=fac_user.id,
        reason_code="FACULTY_COMMIT",
    )
    db_session.add(rec)
    db_session.flush()

    # 2. Authorization Guard: Unassigned faculty rejected (403)
    user_other = User(email="other_faculty@kucet.ac.in", hashed_password="pw", role=UserRole.FACULTY)
    db_session.add(user_other)
    db_session.flush()
    faculty_other = Faculty(user_id=user_other.id, employee_id="FAC-OTHER-99", full_name="Other Faculty", department_id=seed_data["department"].id)
    db_session.add(faculty_other)
    db_session.flush()

    with pytest.raises(PermissionDeniedError):
        CommitService.apply_attendance_correction(
            db=db_session,
            session_id=session.id,
            user=user_other,
            request=correction_req,
            correlation_id="corr-inv-02",
        )

    # 3. Identical status transition rejected
    with pytest.raises(ValueError, match="already marked as"):
        CommitService.apply_attendance_correction(
            db=db_session,
            session_id=session.id,
            user=fac_user,
            request=correction_req,  # already PRESENT_CONFIRMED
            correlation_id="corr-inv-03",
        )

