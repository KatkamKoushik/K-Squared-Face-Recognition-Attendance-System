"""
K² FRS — Attendance Denominator Arithmetic & Reporting Service.
Enforces that attendance percentage is calculated per student per conducted instructional unit.
Zero denominator yields None (N/A) rather than misleading 0% or 100%.
"""

from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.domain.enums import AttendanceStatus, UnitStatus, EnrollmentStatus
from app.domain.models.academic import SubjectOffering
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot, SnapshotStudentItem
from app.domain.models.student import Student, Enrollment
from app.domain.models.attendance import AttendanceRecord
from app.schemas.attendance import (
    StudentAttendanceStat,
    OfferingAttendanceAnalyticsResponse,
)


class AnalyticsService:

    @staticmethod
    def get_offering_attendance_analytics(
        db: Session,
        offering_id: str,
    ) -> OfferingAttendanceAnalyticsResponse:
        """
        Calculates authoritative institutional attendance stats from committed records.
        Enforces per-student eligibility: denominator is derived from student's inclusion
        in the frozen session roster snapshots and conducted units.
        """
        resolved_offering_id = offering_id
        offering = db.get(SubjectOffering, offering_id)
        if not offering:
            from app.domain.models.academic import Subject
            code_candidate = offering_id.replace("OFF-", "").split("-")[0]
            matched = (
                db.execute(
                    select(SubjectOffering.id)
                    .join(Subject, Subject.id == SubjectOffering.subject_id)
                    .where(Subject.code.ilike(f"%{code_candidate}%"))
                ).scalars().first()
            )
            if matched:
                resolved_offering_id = matched

        conducted_units_stmt = (
            select(func.count(AttendanceUnit.id))
            .join(AttendanceSession, AttendanceSession.id == AttendanceUnit.session_id)
            .where(
                and_(
                    AttendanceSession.offering_id == resolved_offering_id,
                    AttendanceUnit.is_conducted == True,
                    AttendanceUnit.status == UnitStatus.COMMITTED,
                )
            )
        )
        total_conducted = db.execute(conducted_units_stmt).scalar() or 0

        sessions_stmt = select(func.count(AttendanceSession.id)).where(
            and_(
                AttendanceSession.offering_id == resolved_offering_id,
                AttendanceSession.finalized_at.isnot(None),
            )
        )
        total_sessions = db.execute(sessions_stmt).scalar() or 0

        # Check if snapshots exist for this offering
        snapshots_exist = (
            db.execute(
                select(func.count(RosterSnapshot.id))
                .join(AttendanceSession, AttendanceSession.id == RosterSnapshot.session_id)
                .where(AttendanceSession.offering_id == resolved_offering_id)
            ).scalar()
            or 0
        )

        students_stmt = (
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(
                and_(
                    Enrollment.offering_id == resolved_offering_id,
                    Enrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
            .order_by(Student.roll_number)
        )
        students = list(db.execute(students_stmt).scalars().all())

        student_stats: List[StudentAttendanceStat] = []

        for student in students:
            attended_stmt = (
                select(func.count(AttendanceRecord.id))
                .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
                .where(
                    and_(
                        AttendanceSession.offering_id == resolved_offering_id,
                        AttendanceRecord.student_id == student.id,
                        AttendanceRecord.status == AttendanceStatus.PRESENT_CONFIRMED,
                    )
                )
            )
            attended_count = db.execute(attended_stmt).scalar() or 0

            # Derive eligible conducted units for this specific student
            if snapshots_exist > 0:
                student_eligible_stmt = (
                    select(func.count(AttendanceUnit.id))
                    .join(AttendanceSession, AttendanceSession.id == AttendanceUnit.session_id)
                    .join(RosterSnapshot, RosterSnapshot.session_id == AttendanceSession.id)
                    .join(SnapshotStudentItem, SnapshotStudentItem.snapshot_id == RosterSnapshot.id)
                    .where(
                        and_(
                            AttendanceSession.offering_id == resolved_offering_id,
                            AttendanceSession.finalized_at.isnot(None),
                            SnapshotStudentItem.student_id == student.id,
                            AttendanceUnit.is_conducted == True,
                            AttendanceUnit.status == UnitStatus.COMMITTED,
                        )
                    )
                )
                student_eligible_units = db.execute(student_eligible_stmt).scalar() or 0
            else:
                student_eligible_units = total_conducted

            # K² FRS Denominator rule:
            # If eligible conducted units = 0 -> N/A (None)
            if student_eligible_units == 0:
                pct = None
            else:
                pct = round((attended_count / student_eligible_units) * 100.0, 2)

            student_stats.append(
                StudentAttendanceStat(
                    student_id=student.id,
                    roll_number=student.roll_number,
                    full_name=student.full_name,
                    attended_conducted_units=attended_count,
                    eligible_conducted_units=student_eligible_units,
                    attendance_percent=pct,
                )
            )

        return OfferingAttendanceAnalyticsResponse(
            offering_id=resolved_offering_id,
            total_sessions=total_sessions,
            total_conducted_units=total_conducted,
            student_stats=student_stats,
        )
