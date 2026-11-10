"""
FRS V7.1 K² — Atomic Attendance Commit & Idempotency Receipt Service.
Executes an ACID transaction binding student-unit attendance records,
durable receipts, and append-only audit events.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import json
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload, Session
from app.core.config import settings
from app.core.errors import (
    PermissionDeniedError,
    ResourceNotFoundError,
    StateTransitionError,
    IdempotencyConflictError,
)
from app.domain.enums import SessionState, UnitStatus, AuditAction, AttendanceStatus, UserRole
from app.domain.models.academic import User, Faculty
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent
from app.schemas.attendance import (
    AttendanceCommitRequest,
    CommitReceiptResponse,
    AttendanceCorrectionRequest,
    AttendanceCorrectionResponse,
    ReceiptVerificationResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommitService:

    @staticmethod
    def compute_receipt_signature(payload: dict) -> str:
        """Computes authoritative server HMAC-SHA256 signature for commit receipts."""
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        secret_bytes = settings.SECRET_KEY.encode("utf-8")
        return hmac.new(secret_bytes, canonical_bytes, hashlib.sha256).hexdigest()

    @staticmethod
    def commit_session_attendance(
        db: Session,
        session_id: str,
        user_id: str,
        faculty_id: str,
        request: AttendanceCommitRequest,
        correlation_id: str,
    ) -> CommitReceipt:
        """
        Executes atomic ACID commit of finalized per-unit attendance.
        1. Validates session existence & faculty authorization (IDOR safe).
        2. Checks idempotency.
        3. Enforces session state (must be IN_REVIEW).
        4. Validates decisions against immutable roster snapshot and ensures tuple uniqueness.
        5. Persists attendance rows per student per conducted unit.
        6. Issues durable cryptographically anchored receipt.
        7. Emits append-only audit event.
        """
        # 1. Idempotency Check
        receipt_stmt = select(CommitReceipt).where(
            CommitReceipt.idempotency_key == request.idempotency_key
        )
        existing_receipt = db.execute(receipt_stmt).scalar_one_or_none()
        if existing_receipt:
            if existing_receipt.session_id != session_id:
                raise IdempotencyConflictError(
                    key=request.idempotency_key,
                    message="Idempotency key was previously used for a different session.",
                )
            # Replay authorization guard: verify caller is the conducting faculty owner
            session_owner_stmt = select(AttendanceSession.faculty_id).where(AttendanceSession.id == session_id)
            owner_faculty_id = db.execute(session_owner_stmt).scalar_one_or_none()
            if owner_faculty_id != faculty_id:
                raise PermissionDeniedError(
                    message="Only the conducting faculty member may access this commit receipt.",
                    reason_code="FACULTY_MISMATCH",
                )
            return existing_receipt  # Return original durable receipt safely

        # 2. Fetch session and validate faculty ownership for new commit
        session_stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.units),
                selectinload(AttendanceSession.snapshot).selectinload(RosterSnapshot.items),
            )
            .where(AttendanceSession.id == session_id)
        )
        session = db.execute(session_stmt).scalar_one_or_none()
        if not session:
            raise ResourceNotFoundError("AttendanceSession", session_id)

        if session.faculty_id != faculty_id:
            raise PermissionDeniedError(
                message="Only the conducting faculty member may commit attendance for this session.",
                reason_code="FACULTY_MISMATCH",
            )

        # 3. State Machine Guardrail
        current_state_str = session.state.value if hasattr(session.state, "value") else str(session.state)
        finalized_val = SessionState.FINALIZED.value if hasattr(SessionState.FINALIZED, "value") else str(SessionState.FINALIZED)
        in_review_val = SessionState.IN_REVIEW.value if hasattr(SessionState.IN_REVIEW, "value") else str(SessionState.IN_REVIEW)

        if current_state_str == finalized_val:
            raise StateTransitionError(
                message="Attendance for this session has already been finalized.",
                current_state=current_state_str,
                attempted_state="FINALIZED",
                reason_code="SESSION_ALREADY_FINALIZED",
            )

        if current_state_str != in_review_val:
            raise StateTransitionError(
                message=f"Session must be in IN_REVIEW state before attendance can be committed (current: {current_state_str}).",
                current_state=current_state_str,
                attempted_state="FINALIZED",
                reason_code="ILLEGAL_STATE_TRANSITION",
            )

        # 4. Resolve units mapping & validate roster snapshot membership
        unit_map = {u.unit_index: u for u in session.units}
        for u_idx in request.conducted_unit_indices:
            if u_idx not in unit_map:
                raise ValueError(f"Conducted unit index {u_idx} was not planned in session {session_id}")

        eligible_student_ids = {item.student_id for item in session.snapshot.items} if session.snapshot else set()

        seen_decisions = set()
        total_present = 0
        total_absent = 0
        records_to_add = []

        for decision in request.decisions:
            if decision.unit_index not in request.conducted_unit_indices:
                continue

            # Verify student belongs to frozen roster snapshot
            if eligible_student_ids and decision.student_id not in eligible_student_ids:
                raise ValueError(
                    f"Student {decision.student_id} is not present in the frozen roster snapshot for session {session_id}"
                )

            # Prevent duplicate student-unit tuples
            decision_key = (decision.student_id, decision.unit_index)
            if decision_key in seen_decisions:
                raise ValueError(
                    f"Duplicate attendance decision for student {decision.student_id} in unit {decision.unit_index}"
                )
            seen_decisions.add(decision_key)

            unit_entity = unit_map[decision.unit_index]
            rec = AttendanceRecord(
                session_id=session.id,
                unit_id=unit_entity.id,
                student_id=decision.student_id,
                status=decision.status,
                finalized_by_user_id=user_id,
                reason_code=decision.reason_code,
                source_evidence_id=decision.source_evidence_id,
            )
            records_to_add.append(rec)
            if decision.status == AttendanceStatus.PRESENT_CONFIRMED:
                total_present += 1
            elif decision.status == AttendanceStatus.ABSENT_CONFIRMED:
                total_absent += 1
            # Note: EXCUSED is strictly not counted in total_absent

        # Invariant FR-08: Decision Matrix Completeness
        # Cartesian product of eligible_student_ids x conducted_unit_indices must be fully decided
        if eligible_student_ids and request.conducted_unit_indices:
            expected_pairs = {
                (student_id, unit_idx)
                for student_id in eligible_student_ids
                for unit_idx in request.conducted_unit_indices
            }
            missing_pairs = expected_pairs - seen_decisions
            if missing_pairs:
                missing_students_count = len({s for s, _ in missing_pairs})
                raise ValueError(
                    f"Incomplete attendance decision matrix. Missing decisions for {len(missing_pairs)} student-unit "
                    f"combinations ({missing_students_count} students affected across {len(request.conducted_unit_indices)} conducted units). "
                    "Every eligible student in the frozen roster snapshot must have an explicit status confirmed for every conducted unit."
                )

        db.add_all(records_to_add)

        # Update unit states
        for u in session.units:
            if u.unit_index in request.conducted_unit_indices:
                u.is_conducted = True
                u.status = UnitStatus.COMMITTED
            else:
                u.is_conducted = False
                u.status = UnitStatus.NOT_CONDUCTED

        # Update session state
        session.state = SessionState.FINALIZED
        session.finalized_at = utc_now()

        # 5. Build Receipt Signature
        receipt_payload = {
            "session_id": session_id,
            "idempotency_key": request.idempotency_key,
            "user_id": user_id,
            "total_conducted": len(request.conducted_unit_indices),
            "total_present": total_present,
            "total_absent": total_absent,
            "timestamp": session.finalized_at.isoformat(),
        }
        receipt_hash = CommitService.compute_receipt_signature(receipt_payload)

        receipt = CommitReceipt(
            session_id=session_id,
            idempotency_key=request.idempotency_key,
            committed_by_user_id=user_id,
            total_conducted_units=len(request.conducted_unit_indices),
            total_present_records=total_present,
            total_absent_records=total_absent,
            receipt_hash=receipt_hash,
            committed_at=session.finalized_at,
        )
        db.add(receipt)

        # 6. Append-only Audit Event
        audit = AuditEvent(
            session_id=session_id,
            actor_id=user_id,
            action=AuditAction.ATTENDANCE_COMMITTED,
            reason="Faculty explicitly confirmed and committed instructional unit attendance.",
            before_state={"state": SessionState.IN_REVIEW.value},
            after_state={"state": SessionState.FINALIZED.value, "receipt_hash": receipt_hash},
            correlation_id=correlation_id,
        )
        db.add(audit)

        db.flush()
        return receipt

    @staticmethod
    def get_session_receipt(
        db: Session,
        session_id: str,
        user: User,
    ) -> CommitReceipt:
        """
        Retrieves the durable commit receipt for a finalized session.
        Enforces that only the conducting faculty owner or an administrator can access it.
        """
        receipt_stmt = select(CommitReceipt).where(CommitReceipt.session_id == session_id)
        receipt = db.execute(receipt_stmt).scalar_one_or_none()
        if not receipt:
            raise ResourceNotFoundError(resource="CommitReceipt", identifier=session_id)

        if user.role != UserRole.ADMIN:
            session = db.get(AttendanceSession, session_id)
            if not session:
                raise ResourceNotFoundError(resource="AttendanceSession", identifier=session_id)

            faculty_stmt = select(Faculty).where(Faculty.user_id == user.id)
            faculty = db.execute(faculty_stmt).scalar_one_or_none()
            if not faculty or session.faculty_id != faculty.id:
                raise PermissionDeniedError(
                    message="Only the conducting faculty member or an administrator may access this commit receipt.",
                    reason_code="FACULTY_MISMATCH",
                )
        return receipt

    @staticmethod
    def apply_attendance_correction(
        db: Session,
        session_id: str,
        user: User,
        request: AttendanceCorrectionRequest,
        correlation_id: str,
    ) -> AttendanceCorrectionResponse:
        """
        Applies an audited post-commit attendance correction or processes an official student appeal.
        Enforces:
        1. Caller authorization: conducting faculty or administrator only (IDOR safe).
        2. Session state must be FINALIZED.
        3. Unit must be a conducted unit within this session.
        4. AttendanceRecord must exist for (session_id, unit_id, student_id).
        5. Emits an immutable AuditEvent (POST_COMMIT_OVERRIDE or APPEAL_PROCESSED) with before/after state.
        6. Reconciles CommitReceipt aggregate metrics.
        """
        session_stmt = (
            select(AttendanceSession)
            .options(selectinload(AttendanceSession.units))
            .where(AttendanceSession.id == session_id)
        )
        session = db.execute(session_stmt).scalar_one_or_none()
        if not session:
            raise ResourceNotFoundError(resource="AttendanceSession", identifier=session_id)

        # 1. Authorization Guard
        if user.role != UserRole.ADMIN:
            faculty = db.execute(
                select(Faculty).where(Faculty.user_id == user.id)
            ).scalar_one_or_none()
            if not faculty or session.faculty_id != faculty.id:
                raise PermissionDeniedError(
                    message="Only the conducting faculty member or an administrator may apply attendance corrections.",
                    reason_code="FACULTY_MISMATCH",
                )

        # 2. State Guard
        curr_state_val = session.state.value if hasattr(session.state, "value") else str(session.state)
        fin_val = SessionState.FINALIZED.value if hasattr(SessionState.FINALIZED, "value") else str(SessionState.FINALIZED)
        if curr_state_val != fin_val:
            raise StateTransitionError(
                message=f"Attendance corrections can only be applied to FINALIZED sessions (current state: {curr_state_val}).",
                current_state=curr_state_val,
                attempted_state="FINALIZED",
                reason_code="SESSION_NOT_FINALIZED",
            )

        # 3. Unit validation
        unit = next((u for u in session.units if u.unit_index == request.unit_index and u.is_conducted), None)
        if not unit:
            raise ValueError(f"Unit index {request.unit_index} was not conducted in session {session_id}")

        # 4. Find record
        record_stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.unit_id == unit.id,
                AttendanceRecord.student_id == request.student_id,
            )
        )
        record = db.execute(record_stmt).scalar_one_or_none()
        if not record:
            raise ResourceNotFoundError(
                resource="AttendanceRecord",
                identifier=f"student={request.student_id}, unit={request.unit_index}",
            )

        previous_status = record.status
        if previous_status == request.new_status:
            raise ValueError(
                f"Student attendance is already marked as {request.new_status.value} for unit {request.unit_index}."
            )

        action_type = request.action_type.upper().strip()
        if action_type not in ["OVERRIDE", "APPEAL"]:
            raise ValueError("action_type must be either 'OVERRIDE' or 'APPEAL'")

        action = AuditAction.POST_COMMIT_OVERRIDE if action_type == "OVERRIDE" else AuditAction.APPEAL_PROCESSED

        # 5. Mutate record with audit lineage
        record.status = request.new_status
        record.finalized_by_user_id = user.id
        record.reason_code = f"AUDIT_{action_type}"

        # 6. Reconcile CommitReceipt counts if receipt exists
        receipt_stmt = select(CommitReceipt).where(CommitReceipt.session_id == session_id)
        receipt = db.execute(receipt_stmt).scalar_one_or_none()
        if receipt:
            if previous_status == AttendanceStatus.PRESENT_CONFIRMED:
                receipt.total_present_records = max(0, receipt.total_present_records - 1)
            elif previous_status == AttendanceStatus.ABSENT_CONFIRMED:
                receipt.total_absent_records = max(0, receipt.total_absent_records - 1)

            if request.new_status == AttendanceStatus.PRESENT_CONFIRMED:
                receipt.total_present_records += 1
            elif request.new_status == AttendanceStatus.ABSENT_CONFIRMED:
                receipt.total_absent_records += 1

        # 7. Append immutable AuditEvent
        now = utc_now()
        prev_val = previous_status.value if hasattr(previous_status, "value") else str(previous_status)
        new_val = request.new_status.value if hasattr(request.new_status, "value") else str(request.new_status)
        action_val = action.value if hasattr(action, "value") else str(action)

        audit_event = AuditEvent(
            session_id=session_id,
            actor_id=user.id,
            action=action,
            reason=f"[{action_type}] {request.reason}" + (f" (Ref: {request.reference_document})" if request.reference_document else ""),
            before_state={"status": prev_val, "reason_code": "FACULTY_COMMIT"},
            after_state={"status": new_val, "reference_document": request.reference_document},
            correlation_id=correlation_id,
            timestamp=now,
        )
        db.add(audit_event)
        db.flush()

        return AttendanceCorrectionResponse(
            record_id=record.id,
            session_id=session_id,
            student_id=request.student_id,
            unit_index=request.unit_index,
            previous_status=previous_status,
            new_status=request.new_status,
            action=action_val,
            audit_event_id=audit_event.id,
            updated_at=now,
        )

    @staticmethod
    def verify_session_receipt(
        db: Session,
        session_id: str,
        user: User,
    ) -> ReceiptVerificationResponse:
        """
        Cryptographically verifies the authenticity and ledger consistency of a commit receipt.
        Recomputes HMAC signature and cross-checks actual database attendance records.
        """
        receipt_stmt = select(CommitReceipt).where(CommitReceipt.session_id == session_id)
        receipt = db.execute(receipt_stmt).scalar_one_or_none()
        if not receipt:
            raise ResourceNotFoundError(resource="CommitReceipt", identifier=session_id)

        if user.role != UserRole.ADMIN:
            session = db.get(AttendanceSession, session_id)
            if not session:
                raise ResourceNotFoundError(resource="AttendanceSession", identifier=session_id)
            faculty = db.execute(
                select(Faculty).where(Faculty.user_id == user.id)
            ).scalar_one_or_none()
            if not faculty or session.faculty_id != faculty.id:
                raise PermissionDeniedError(
                    message="Only the conducting faculty member or an administrator may verify this receipt.",
                    reason_code="FACULTY_MISMATCH",
                )

        # 1. Recompute expected HMAC and fallback legacy SHA256
        payload = {
            "session_id": session_id,
            "idempotency_key": receipt.idempotency_key,
            "user_id": receipt.committed_by_user_id,
            "total_conducted": receipt.total_conducted_units,
            "total_present": receipt.total_present_records,
            "total_absent": receipt.total_absent_records,
            "timestamp": receipt.committed_at.isoformat(),
        }
        expected_hmac = CommitService.compute_receipt_signature(payload)
        expected_sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

        signature_verified = (receipt.receipt_hash in [expected_hmac, expected_sha256])

        # 2. Check ledger consistency against actual database rows
        present_count = db.execute(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.status == AttendanceStatus.PRESENT_CONFIRMED,
            )
        ).scalar() or 0

        absent_count = db.execute(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.status == AttendanceStatus.ABSENT_CONFIRMED,
            )
        ).scalar() or 0

        ledger_matched = (
            present_count == receipt.total_present_records and absent_count == receipt.total_absent_records
        )

        return ReceiptVerificationResponse(
            session_id=session_id,
            receipt_id=receipt.id,
            is_valid=signature_verified and ledger_matched,
            signature_verified=signature_verified,
            ledger_records_matched=ledger_matched,
            total_conducted_units=receipt.total_conducted_units,
            total_present_records=receipt.total_present_records,
            total_absent_records=receipt.total_absent_records,
            receipt_hash=receipt.receipt_hash,
            verified_at=utc_now(),
        )
