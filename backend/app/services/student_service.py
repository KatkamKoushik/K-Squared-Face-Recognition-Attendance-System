"""
FRS V7.1 K² — Student Portal Service.
Provides authoritative, isolated data access for student identity, enrolled attendance,
and formal academic appeals without cross-student data leakage.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ResourceNotFoundError, PermissionDeniedError, BusinessRuleViolationError
from app.domain.enums import UserRole, AttendanceStatus, AppealStatus, SessionState, AuditAction
from app.domain.models.academic import User, SubjectOffering, Subject, Cohort, Faculty
from app.domain.models.student import Student, Enrollment
from app.domain.models.session import AttendanceSession, AttendanceUnit
from app.domain.models.attendance import AttendanceRecord, AttendanceAppeal
from app.domain.models.audit import AuditEvent
from app.schemas.attendance import AttendanceAppealCreate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StudentService:

    @staticmethod
    def get_student_for_user(db: Session, user: User) -> Student:
        """Resolves the authoritative Student profile associated with the authenticated user."""
        student = db.execute(
            select(Student)
            .options(selectinload(Student.cohort))
            .where(Student.institutional_email == user.email)
        ).scalar_one_or_none()

        if not student:
            # Fallback check if user ID matches roll number or email prefix
            roll_prefix = user.email.split("@")[0].upper()
            student = db.execute(
                select(Student)
                .options(selectinload(Student.cohort))
                .where(Student.roll_number == roll_prefix)
            ).scalar_one_or_none()

        if not student:
            raise ResourceNotFoundError(
                resource="StudentProfile",
                identifier=user.email,
            )
        return student

    @staticmethod
    def get_attendance_summary(db: Session, student: Student) -> List[Dict[str, Any]]:
        """
        Calculates per-subject attendance according to the official institutional denominator rule:
        Percentage = (Attended Conducted Units / Eligible Conducted Units) * 100
        """
        # 1. Fetch active enrollments
        enrollments = db.execute(
            select(Enrollment)
            .where(
                and_(
                    Enrollment.student_id == student.id,
                    Enrollment.status == "ACTIVE",
                )
            )
        ).scalars().all()

        summary: List[Dict[str, Any]] = []

        for enr in enrollments:
            offering = db.execute(
                select(SubjectOffering)
                .options(selectinload(SubjectOffering.subject), selectinload(SubjectOffering.term))
                .where(SubjectOffering.id == enr.offering_id)
            ).scalar_one_or_none()

            if not offering:
                continue

            # Find all finalized sessions for this offering
            sessions = db.execute(
                select(AttendanceSession)
                .options(selectinload(AttendanceSession.units))
                .where(
                    and_(
                        AttendanceSession.offering_id == offering.id,
                        AttendanceSession.state == SessionState.FINALIZED,
                    )
                )
            ).scalars().all()

            eligible_conducted_units = 0
            session_ids = []
            for s in sessions:
                session_ids.append(s.id)
                eligible_conducted_units += sum(1 for u in s.units if u.is_conducted)

            attended_conducted_units = 0
            if session_ids:
                attended_records = db.execute(
                    select(AttendanceRecord).where(
                        and_(
                            AttendanceRecord.student_id == student.id,
                            AttendanceRecord.session_id.in_(session_ids),
                            AttendanceRecord.status.in_([
                                AttendanceStatus.PRESENT_CONFIRMED,
                                AttendanceStatus.EXCUSED,
                            ]),
                        )
                    )
                ).scalars().all()
                attended_conducted_units = len(attended_records)

            percent = None
            status_label = "NOT_EVALUATED"
            if eligible_conducted_units > 0:
                percent = round((attended_conducted_units / eligible_conducted_units) * 100.0, 2)
                if percent >= 75.0:
                    status_label = "ELIGIBLE"
                elif percent >= 65.0:
                    status_label = "CONDONATION_REQUIRED"
                else:
                    status_label = "DETENTION_RISK"

            summary.append({
                "offering_id": offering.id,
                "subject_code": offering.subject.code if offering.subject else "SUB",
                "subject_name": offering.subject.name if offering.subject else "Subject Offering",
                "section": offering.section,
                "total_sessions": len(sessions),
                "eligible_conducted_units": eligible_conducted_units,
                "attended_conducted_units": attended_conducted_units,
                "attendance_percent": percent,
                "eligibility_status": status_label,
            })

        return summary

    @staticmethod
    def get_offering_ledger(db: Session, student: Student, offering_id: str) -> Dict[str, Any]:
        """Returns the granular, unit-level attendance history for a single offering."""
        offering = db.execute(
            select(SubjectOffering)
            .options(selectinload(SubjectOffering.subject))
            .where(SubjectOffering.id == offering_id)
        ).scalar_one_or_none()

        if not offering:
            raise ResourceNotFoundError(resource="SubjectOffering", identifier=offering_id)

        sessions = db.execute(
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.units),
                selectinload(AttendanceSession.attendance_records),
            )
            .where(
                and_(
                    AttendanceSession.offering_id == offering_id,
                    AttendanceSession.state == SessionState.FINALIZED,
                )
            )
            .order_by(AttendanceSession.session_date.desc())
        ).scalars().all()

        ledger_sessions = []
        for s in sessions:
            student_records = {
                r.unit_id: r for r in s.attendance_records if r.student_id == student.id
            }

            units_data = []
            for u in sorted(s.units, key=lambda x: x.unit_index):
                rec = student_records.get(u.id)
                rec_status = rec.status.value if rec and hasattr(rec.status, "value") else (str(rec.status) if rec else "NOT_RECORDED")
                units_data.append({
                    "unit_id": u.id,
                    "unit_index": u.unit_index,
                    "is_conducted": u.is_conducted,
                    "status": rec_status,
                    "reason_code": rec.reason_code if rec else None,
                })

            ledger_sessions.append({
                "session_id": s.id,
                "session_date": s.session_date.isoformat(),
                "units": units_data,
            })

        return {
            "offering_id": offering.id,
            "subject_code": offering.subject.code if offering.subject else "SUB",
            "subject_name": offering.subject.name if offering.subject else "Subject",
            "sessions": ledger_sessions,
        }

    @staticmethod
    def submit_appeal(
        db: Session,
        student: Student,
        data: AttendanceAppealCreate,
        correlation_id: str,
    ) -> AttendanceAppeal:
        """Submits a formal student attendance appeal for an absent unit."""
        session = db.execute(
            select(AttendanceSession).where(AttendanceSession.id == data.session_id)
        ).scalar_one_or_none()

        if not session or session.state != SessionState.FINALIZED:
            raise BusinessRuleViolationError(
                message="Appeals can only be submitted for FINALIZED attendance sessions.",
                reason_code="INVALID_SESSION_STATE",
            )

        unit = db.execute(
            select(AttendanceUnit).where(
                and_(
                    AttendanceUnit.id == data.unit_id,
                    AttendanceUnit.session_id == data.session_id,
                    AttendanceUnit.is_conducted == True,
                )
            )
        ).scalar_one_or_none()

        if not unit:
            raise ResourceNotFoundError(resource="AttendanceUnit", identifier=data.unit_id)

        # Check existing record
        record = db.execute(
            select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.session_id == data.session_id,
                    AttendanceRecord.unit_id == data.unit_id,
                    AttendanceRecord.student_id == student.id,
                )
            )
        ).scalar_one_or_none()

        if not record:
            raise BusinessRuleViolationError(
                message="No attendance record found for student in this session unit.",
                reason_code="ATTENDANCE_RECORD_NOT_FOUND",
            )

        appeal = AttendanceAppeal(
            student_id=student.id,
            session_id=data.session_id,
            unit_id=data.unit_id,
            reason=data.reason,
            evidence_path=data.evidence_path,
            status=AppealStatus.PENDING,
        )
        db.add(appeal)
        db.flush()

        audit = AuditEvent(
            session_id=data.session_id,
            actor_id=student.id,
            action=AuditAction.APPEAL_PROCESSED,
            reason=f"Student appeal submitted: {data.reason[:100]}",
            before_state={"record_status": str(record.status)},
            after_state={"appeal_id": appeal.id, "appeal_status": AppealStatus.PENDING.value},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.commit()
        db.refresh(appeal)
        return appeal

    @staticmethod
    def list_student_appeals(db: Session, student: Student) -> List[AttendanceAppeal]:
        """Lists all appeals submitted by the student."""
        result = db.execute(
            select(AttendanceAppeal)
            .where(AttendanceAppeal.student_id == student.id)
            .order_by(AttendanceAppeal.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def list_all_appeals(
        db: Session,
        status: Optional[AppealStatus] = None,
        limit: int = 100,
    ) -> List[AttendanceAppeal]:
        """Administrative method: lists all pending or reviewed student appeals."""
        stmt = select(AttendanceAppeal).order_by(AttendanceAppeal.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(AttendanceAppeal.status == status)
        result = db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def review_appeal(
        db: Session,
        appeal_id: str,
        reviewer: User,
        approved: bool,
        review_notes: str,
        correlation_id: str,
    ) -> AttendanceAppeal:
        """Administrative method: reviews and decides an attendance appeal."""
        appeal = db.execute(
            select(AttendanceAppeal).where(AttendanceAppeal.id == appeal_id)
        ).scalar_one_or_none()

        if not appeal:
            raise ResourceNotFoundError(resource="AttendanceAppeal", identifier=appeal_id)

        appeal.status = AppealStatus.APPROVED if approved else AppealStatus.REJECTED
        appeal.review_notes = review_notes
        appeal.reviewed_by_user_id = reviewer.id
        appeal.reviewed_at = utc_now()

        if approved:
            # Update the attendance record to EXCUSED
            record = db.execute(
                select(AttendanceRecord).where(
                    and_(
                        AttendanceRecord.session_id == appeal.session_id,
                        AttendanceRecord.unit_id == appeal.unit_id,
                        AttendanceRecord.student_id == appeal.student_id,
                    )
                )
            ).scalar_one_or_none()
            if record:
                record.status = AttendanceStatus.EXCUSED
                record.reason_code = f"APPEAL_APPROVED: {review_notes[:40]}"

        audit = AuditEvent(
            session_id=appeal.session_id,
            actor_id=reviewer.id,
            action=AuditAction.APPEAL_PROCESSED,
            reason=f"Appeal {appeal_id} decision: {appeal.status.value}",
            before_state={"appeal_status": AppealStatus.PENDING.value},
            after_state={"appeal_status": appeal.status.value, "approved": approved},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.commit()
        db.refresh(appeal)
        return appeal
