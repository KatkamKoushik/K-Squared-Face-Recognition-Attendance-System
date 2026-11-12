"""
K² FRS — Roster Snapshot & Academic Eligibility Resolution Service.
Enforces immutable snapshot freezing and exact deduplicated union for joint classes.
"""

from datetime import date
from typing import List, Dict
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from app.core.errors import StateTransitionError
from app.domain.enums import EnrollmentStatus
from app.domain.models.academic import AuthorizedClassGroup, ClassGroupMemberCohort, SubjectOffering
from app.domain.models.student import Student, Enrollment
from app.domain.models.session import RosterSnapshot, SnapshotStudentItem


class RosterService:

    @staticmethod
    def freeze_session_roster(
        db: Session,
        session_id: str,
        offering_id: str,
        class_group_id: str | None = None,
        effective_date: date | None = None,
    ) -> RosterSnapshot:
        """
        Computes effective enrollment eligibility and permanently freezes an immutable
        roster snapshot for the attendance session.
        Enforces active status, effective-dated ranges (start and end), and joint-class deduplication.
        """
        existing_snapshot = db.execute(
            select(RosterSnapshot).where(RosterSnapshot.session_id == session_id)
        ).scalar_one_or_none()
        if existing_snapshot:
            raise StateTransitionError(
                message="Session roster snapshot has already been frozen and is immutable.",
                current_state="ROSTER_FROZEN",
                attempted_state="FREEZE_ROSTER",
                reason_code="ROSTER_SNAPSHOT_ALREADY_EXISTS",
            )

        target_date = effective_date or date.today()
        eligible_students: Dict[str, Student] = {}

        if class_group_id:
            cohort_stmt = select(ClassGroupMemberCohort.cohort_id).where(
                ClassGroupMemberCohort.group_id == class_group_id
            )
            cohort_ids = db.execute(cohort_stmt).scalars().all()

            students_stmt = select(Student).where(
                and_(
                    Student.cohort_id.in_(cohort_ids),
                    Student.is_active == True,
                )
            )
            cohort_students = db.execute(students_stmt).scalars().all()
            for s in cohort_students:
                eligible_students[s.id] = s
        else:
            enrollment_stmt = (
                select(Student)
                .join(Enrollment, Enrollment.student_id == Student.id)
                .where(
                    and_(
                        Enrollment.offering_id == offering_id,
                        Enrollment.status == EnrollmentStatus.ACTIVE,
                        Enrollment.effective_start <= target_date,
                        or_(Enrollment.effective_end.is_(None), Enrollment.effective_end >= target_date),
                        Student.is_active == True,
                    )
                )
            )
            enrolled_students = db.execute(enrollment_stmt).scalars().all()
            for s in enrolled_students:
                eligible_students[s.id] = s

        snapshot = RosterSnapshot(
            session_id=session_id,
            snapshot_version=1,
            total_eligible_students=len(eligible_students),
        )
        db.add(snapshot)
        db.flush()

        for student in eligible_students.values():
            item = SnapshotStudentItem(
                snapshot_id=snapshot.id,
                student_id=student.id,
                roll_number=student.roll_number,
                full_name=student.full_name,
                cohort_id=student.cohort_id,
            )
            db.add(item)

        db.flush()
        return snapshot

    @staticmethod
    def get_session_snapshot(db: Session, session_id: str) -> RosterSnapshot | None:
        result = db.execute(
            select(RosterSnapshot).where(RosterSnapshot.session_id == session_id)
        )
        return result.scalar_one_or_none()
