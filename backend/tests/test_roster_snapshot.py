"""
FRS V7.1 K² — Immutable Roster Snapshot & Joint-Class Union Tests.
"""

from datetime import date
import pytest
from sqlalchemy.orm import Session
from app.core.errors import StateTransitionError
from app.domain.enums import SessionState
from app.domain.models.session import AttendanceSession
from app.domain.models.academic import AuthorizedClassGroup, ClassGroupMemberCohort
from app.domain.models.student import Student
from app.services.roster_service import RosterService


def test_single_offering_roster_snapshot_freezes_enrolled_students(db_session: Session, seed_data):
    session = AttendanceSession(
        offering_id=seed_data["offering"].id,
        faculty_id=seed_data["faculty"].id,
        state=SessionState.DRAFT,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterService.freeze_session_roster(
        db=db_session,
        session_id=session.id,
        offering_id=seed_data["offering"].id,
    )
    assert snapshot.total_eligible_students == 3
    assert len(snapshot.items) == 3

    roll_numbers = {item.roll_number for item in snapshot.items}
    assert roll_numbers == {"23CSE01", "23CSE02", "23CSE03"}


def test_joint_class_group_roster_union_deduplication(db_session: Session, seed_data):
    """
    Invariants FR-03:
    Joint-class roster union contains exactly eligible students with no duplicate student IDs.
    """
    cohort1 = seed_data["cohort1"]
    cohort2 = seed_data["cohort2"]

    s4 = Student(roll_number="23CSD01", full_name="Kiran Rao", cohort_id=cohort2.id)
    s5 = Student(roll_number="23CSD02", full_name="Sneha Reddy", cohort_id=cohort2.id)
    db_session.add_all([s4, s5])
    db_session.flush()

    group = AuthorizedClassGroup(
        offering_id=seed_data["offering"].id,
        group_name="CSE + CSD Joint OS",
    )
    db_session.add(group)
    db_session.flush()

    m1 = ClassGroupMemberCohort(group_id=group.id, cohort_id=cohort1.id)
    m2 = ClassGroupMemberCohort(group_id=group.id, cohort_id=cohort2.id)
    db_session.add_all([m1, m2])
    db_session.flush()

    session = AttendanceSession(
        offering_id=seed_data["offering"].id,
        class_group_id=group.id,
        faculty_id=seed_data["faculty"].id,
        state=SessionState.DRAFT,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterService.freeze_session_roster(
        db=db_session,
        session_id=session.id,
        offering_id=seed_data["offering"].id,
        class_group_id=group.id,
    )
    assert snapshot.total_eligible_students == 5
    assert len(snapshot.items) == 5

    student_ids = [item.student_id for item in snapshot.items]
    assert len(student_ids) == len(set(student_ids))


def test_roster_snapshot_immutability(db_session: Session, seed_data):
    """Attempting to freeze snapshot on a session that already has one raises StateTransitionError."""
    session = AttendanceSession(
        offering_id=seed_data["offering"].id,
        faculty_id=seed_data["faculty"].id,
        state=SessionState.DRAFT,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    RosterService.freeze_session_roster(
        db=db_session,
        session_id=session.id,
        offering_id=seed_data["offering"].id,
    )

    with pytest.raises(StateTransitionError) as exc_info:
        RosterService.freeze_session_roster(
            db=db_session,
            session_id=session.id,
            offering_id=seed_data["offering"].id,
        )
    assert exc_info.value.reason_code == "ROSTER_SNAPSHOT_ALREADY_EXISTS"
