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
from app.domain.models.student import Student, Enrollment, StudentDataCorrection
from app.domain.models.session import AttendanceSession, AttendanceUnit
from app.domain.models.attendance import AttendanceRecord, AttendanceAppeal
from app.domain.models.audit import AuditEvent, CommitReceipt
from app.schemas.attendance import AttendanceAppealCreate
from app.schemas.events import EventMessage, RealtimeEventType
from app.services.event_broadcaster import broadcaster


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StudentService:

    @staticmethod
    def get_student_for_user(db: Session, user: User) -> Student:
        """Resolves the authoritative Student profile associated with the authenticated user."""
        student = None

        # 1. Direct explicit foreign key relationship
        if user.student_id:
            student = db.execute(
                select(Student)
                .options(selectinload(Student.cohort))
                .where(Student.id == user.student_id)
            ).scalar_one_or_none()

        # 2. Institutional email exact match
        if not student and user.email:
            student = db.execute(
                select(Student)
                .options(selectinload(Student.cohort))
                .where(Student.institutional_email == user.email)
            ).scalar_one_or_none()
            if student and not user.student_id:
                user.student_id = student.id
                db.flush()

        if not student:
            raise ResourceNotFoundError(
                resource="StudentProfile",
                identifier=user.email or user.id,
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

        # Enforce active enrollment ownership (Issue 3)
        target_student_id = student.id if hasattr(student, "id") else student
        enrollment = db.execute(
            select(Enrollment).where(
                and_(
                    Enrollment.student_id == target_student_id,
                    Enrollment.offering_id == offering_id,
                    Enrollment.status == "ACTIVE",
                )
            )
        ).scalar_one_or_none()
        if not enrollment:
            raise PermissionDeniedError(
                message=f"Student {student.roll_number} is not actively enrolled in subject offering {offering_id}.",
                reason_code="OFFERING_ENROLLMENT_REQUIRED",
            )

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

        session_ids = [s.id for s in sessions]
        receipts_map = {}
        if session_ids:
            receipts = db.execute(
                select(CommitReceipt).where(CommitReceipt.session_id.in_(session_ids))
            ).scalars().all()
            for r in receipts:
                receipts_map[r.session_id] = r.receipt_hash

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
                "receipt_hash": receipts_map.get(s.id),
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

        dept_id = student.cohort.department_id if (student and student.cohort) else None
        event_payload = {
            "appeal_id": appeal.id,
            "student_id": student.id,
            "session_id": appeal.session_id,
            "status": "PENDING",
        }
        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ATTENDANCE_APPEALED,
                channel=f"user:{student.id}",
                payload=event_payload,
            )
        )
        if dept_id:
            broadcaster.publish_sync(
                EventMessage(
                    event_type=RealtimeEventType.ATTENDANCE_APPEALED,
                    channel=f"department:{dept_id}",
                    payload=event_payload,
                )
            )

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
        user: Optional[User] = None,
    ) -> List[AttendanceAppeal]:
        """Administrative method: lists student appeals, scoped by department for department admins."""
        stmt = select(AttendanceAppeal).order_by(AttendanceAppeal.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(AttendanceAppeal.status == status)

        if user and user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Department administrator must have an assigned department context.",
                    reason_code="DEPARTMENT_ASSIGNMENT_REQUIRED",
                )
            stmt = (
                stmt.join(Student, AttendanceAppeal.student_id == Student.id)
                .join(Cohort, Student.cohort_id == Cohort.id)
                .where(Cohort.department_id == user.department_id)
            )
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

        # Enforce valid state transition PENDING -> APPROVED / REJECTED (Issue 4)
        if appeal.status != AppealStatus.PENDING:
            raise BusinessRuleViolationError(
                message=f"Appeal {appeal_id} has already been adjudicated with status '{appeal.status}'. Duplicate review is prohibited.",
                reason_code="APPEAL_ALREADY_REVIEWED",
            )

        if reviewer.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            if not reviewer.department_id:
                raise PermissionDeniedError(
                    message="Department administrator must have an assigned department context.",
                    reason_code="DEPARTMENT_ASSIGNMENT_REQUIRED",
                )
            student = db.get(Student, appeal.student_id)
            if not student or not student.cohort or student.cohort.department_id != reviewer.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot review appeals of another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )

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

        appeal_status_val = appeal.status.value if hasattr(appeal.status, "value") else str(appeal.status)
        audit = AuditEvent(
            session_id=appeal.session_id,
            actor_id=reviewer.id,
            action=AuditAction.APPEAL_PROCESSED,
            reason=f"Appeal {appeal_id} decision: {appeal_status_val}",
            before_state={"appeal_status": AppealStatus.PENDING.value if hasattr(AppealStatus.PENDING, "value") else str(AppealStatus.PENDING)},
            after_state={"appeal_status": appeal_status_val, "approved": approved},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.commit()
        db.refresh(appeal)

        dept_id = reviewer.department_id
        event_payload = {
            "appeal_id": appeal.id,
            "student_id": appeal.student_id,
            "session_id": appeal.session_id,
            "status": appeal_status_val,
            "approved": approved,
            "review_notes": review_notes,
        }
        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ATTENDANCE_APPEAL_REVIEWED,
                channel=f"user:{appeal.student_id}",
                payload=event_payload,
            )
        )
        if dept_id:
            broadcaster.publish_sync(
                EventMessage(
                    event_type=RealtimeEventType.ATTENDANCE_APPEAL_REVIEWED,
                    channel=f"department:{dept_id}",
                    payload=event_payload,
                )
            )

        return appeal

    @staticmethod
    def submit_data_correction(
        db: Session,
        student: Student,
        field_name: str,
        requested_value: str,
        reason: str,
        correlation_id: str,
    ) -> StudentDataCorrection:
        """Submits a formal student profile correction request."""
        current_val = None
        if hasattr(student, field_name):
            val = getattr(student, field_name)
            current_val = str(val) if val is not None else None

        correction = StudentDataCorrection(
            student_id=student.id,
            field_name=field_name,
            requested_value=requested_value,
            current_value=current_val,
            reason=reason,
            status="PENDING",
        )
        db.add(correction)
        db.flush()

        audit = AuditEvent(
            session_id=None,
            actor_id=student.id,
            action=AuditAction.CORRECTION_REQUESTED,
            reason=f"Student requested data correction for {field_name}: {reason[:100]}",
            before_state={"field_name": field_name, "current_value": current_val},
            after_state={"correction_id": correction.id, "requested_value": requested_value, "status": "PENDING"},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.commit()
        db.refresh(correction)

        dept_id = student.cohort.department_id if (student and student.cohort) else None
        event_payload = {
            "correction_id": correction.id,
            "student_id": student.id,
            "field_name": field_name,
            "requested_value": requested_value,
            "status": "PENDING",
        }
        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.CORRECTION_SUBMITTED,
                channel=f"user:{student.id}",
                payload=event_payload,
            )
        )
        if dept_id:
            broadcaster.publish_sync(
                EventMessage(
                    event_type=RealtimeEventType.CORRECTION_SUBMITTED,
                    channel=f"department:{dept_id}",
                    payload=event_payload,
                )
            )

        return correction

    @staticmethod
    def list_student_corrections(db: Session, student: Student) -> List[StudentDataCorrection]:
        """Lists all data correction requests submitted by the student."""
        result = db.execute(
            select(StudentDataCorrection)
            .where(StudentDataCorrection.student_id == student.id)
            .order_by(StudentDataCorrection.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def list_all_corrections(
        db: Session,
        status: Optional[str] = None,
        limit: int = 100,
        user: Optional[User] = None,
    ) -> List[StudentDataCorrection]:
        """Administrative method: lists student data correction requests, department-scoped for department admins."""
        stmt = select(StudentDataCorrection).order_by(StudentDataCorrection.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(StudentDataCorrection.status == status)
        if user and user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            if not user.department_id:
                raise PermissionDeniedError(
                    message="Department administrator must have an assigned department context.",
                    reason_code="DEPARTMENT_ASSIGNMENT_REQUIRED",
                )
            stmt = (
                stmt.join(Student, StudentDataCorrection.student_id == Student.id)
                .join(Cohort, Student.cohort_id == Cohort.id)
                .where(Cohort.department_id == user.department_id)
            )
        result = db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def review_data_correction(
        db: Session,
        request_id: str,
        reviewer: User,
        approved: bool,
        review_notes: str,
        correlation_id: str,
    ) -> StudentDataCorrection:
        """Administrative method: reviews and decides a student data correction request."""
        correction = db.get(StudentDataCorrection, request_id)
        if not correction:
            raise ResourceNotFoundError(resource="StudentDataCorrection", identifier=request_id)

        # Enforce valid state transition PENDING -> APPROVED / REJECTED (Issue 4)
        if correction.status != "PENDING":
            raise BusinessRuleViolationError(
                message=f"Data correction request {request_id} has already been adjudicated with status '{correction.status}'. Duplicate review is prohibited.",
                reason_code="CORRECTION_ALREADY_REVIEWED",
            )

        student = db.get(Student, correction.student_id)
        if reviewer.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            if not reviewer.department_id:
                raise PermissionDeniedError(
                    message="Department administrator must have an assigned department context.",
                    reason_code="DEPARTMENT_ASSIGNMENT_REQUIRED",
                )
            if not student or not student.cohort or student.cohort.department_id != reviewer.department_id:
                raise PermissionDeniedError(
                    message="Access denied: Department administrator cannot review data corrections for another department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )

        prev_status = correction.status
        correction.status = "APPROVED" if approved else "REJECTED"
        correction.review_notes = review_notes
        correction.reviewed_by_user_id = reviewer.id
        correction.reviewed_at = utc_now()

        if approved and student:
            if correction.field_name in ("full_name", "institutional_email") and hasattr(student, correction.field_name):
                setattr(student, correction.field_name, correction.requested_value)

        audit = AuditEvent(
            session_id=None,
            actor_id=reviewer.id,
            action=AuditAction.CORRECTION_PROCESSED,
            reason=f"Data correction {request_id} decision: {correction.status}",
            before_state={"correction_status": prev_status},
            after_state={"correction_status": correction.status, "approved": approved, "review_notes": review_notes},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.commit()
        db.refresh(correction)

        dept_id = reviewer.department_id
        event_payload = {
            "correction_id": correction.id,
            "student_id": correction.student_id,
            "status": correction.status,
            "approved": approved,
            "review_notes": review_notes,
        }
        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.CORRECTION_REVIEWED,
                channel=f"user:{correction.student_id}",
                payload=event_payload,
            )
        )
        if dept_id:
            broadcaster.publish_sync(
                EventMessage(
                    event_type=RealtimeEventType.CORRECTION_REVIEWED,
                    channel=f"department:{dept_id}",
                    payload=event_payload,
                )
            )

        return correction
