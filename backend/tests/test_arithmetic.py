"""
FRS V7.1 K² — Attendance Denominator Arithmetic Tests.
Verifies Section 4.2 of V7.1 Blueprint:
attended_units(student, period) = COUNT(finalized unit records with status PRESENT)
conducted_units(period)          = COUNT(authorized unit records confirmed as conducted)
attendance_percent              = 100 * attended_units / eligible_conducted_units
If denominator = 0 -> N/A (None)
"""

import pytest
from sqlalchemy.orm import Session
from app.domain.enums import SessionState, AttendanceStatus, UnitStatus
from app.domain.models.session import AttendanceSession, AttendanceUnit
from app.domain.models.attendance import AttendanceRecord
from app.services.analytics_service import AnalyticsService


def test_zero_denominator_yields_none_na(db_session: Session, seed_data):
    """When eligible conducted units = 0, attendance percentage must be None (N/A), not 0% or 100%."""
    offering = seed_data["offering"]

    analytics = AnalyticsService.get_offering_attendance_analytics(
        db=db_session,
        offering_id=offering.id,
    )
    assert analytics.total_conducted_units == 0
    assert analytics.total_sessions == 0
    assert len(analytics.student_stats) == 3

    for stat in analytics.student_stats:
        assert stat.eligible_conducted_units == 0
        assert stat.attended_conducted_units == 0
        assert stat.attendance_percent is None


def test_exact_unit_denominator_attendance_calculation(db_session: Session, seed_data):
    """
    Evaluates attendance percentage per student across conducted instructional units:
    Session conducts 2 units.
    Student 0: attended units 1 & 2 -> 2/2 = 100%
    Student 1: attended unit 1 only  -> 1/2 = 50%
    Student 2: attended 0 units       -> 0/2 = 0%
    """
    offering = seed_data["offering"]
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    students = seed_data["students"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.FINALIZED,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.COMMITTED)
    u2 = AttendanceUnit(session_id=session.id, unit_index=2, is_conducted=True, status=UnitStatus.COMMITTED)
    db_session.add_all([u1, u2])
    db_session.flush()

    # Student 0: 2/2 present
    r1 = AttendanceRecord(session_id=session.id, unit_id=u1.id, student_id=students[0].id, status=AttendanceStatus.PRESENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    r2 = AttendanceRecord(session_id=session.id, unit_id=u2.id, student_id=students[0].id, status=AttendanceStatus.PRESENT_CONFIRMED, finalized_by_user_id=fac_user.id)

    # Student 1: 1/2 present (Unit 1 present, Unit 2 absent)
    r3 = AttendanceRecord(session_id=session.id, unit_id=u1.id, student_id=students[1].id, status=AttendanceStatus.PRESENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    r4 = AttendanceRecord(session_id=session.id, unit_id=u2.id, student_id=students[1].id, status=AttendanceStatus.ABSENT_CONFIRMED, finalized_by_user_id=fac_user.id)

    # Student 2: 0/2 present (Unit 1 absent, Unit 2 absent)
    r5 = AttendanceRecord(session_id=session.id, unit_id=u1.id, student_id=students[2].id, status=AttendanceStatus.ABSENT_CONFIRMED, finalized_by_user_id=fac_user.id)
    r6 = AttendanceRecord(session_id=session.id, unit_id=u2.id, student_id=students[2].id, status=AttendanceStatus.ABSENT_CONFIRMED, finalized_by_user_id=fac_user.id)

    db_session.add_all([r1, r2, r3, r4, r5, r6])
    db_session.commit()

    analytics = AnalyticsService.get_offering_attendance_analytics(
        db=db_session,
        offering_id=offering.id,
    )
    assert analytics.total_conducted_units == 2

    stats_by_roll = {s.roll_number: s for s in analytics.student_stats}

    assert stats_by_roll["23CSE01"].attended_conducted_units == 2
    assert stats_by_roll["23CSE01"].attendance_percent == 100.0

    assert stats_by_roll["23CSE02"].attended_conducted_units == 1
    assert stats_by_roll["23CSE02"].attendance_percent == 50.0

    assert stats_by_roll["23CSE03"].attended_conducted_units == 0
    assert stats_by_roll["23CSE03"].attendance_percent == 0.0
