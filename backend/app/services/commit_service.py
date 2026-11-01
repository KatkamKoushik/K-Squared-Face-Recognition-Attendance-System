"""
FRS V7.1 K² — Atomic Attendance Commit & Idempotency Receipt Service.
Executes an ACID transaction binding student-unit attendance records,
durable receipts, and append-only audit events.
"""

from datetime import datetime, timezone
import hashlib
import json
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, Session
from app.core.errors import (
    PermissionDeniedError,
    ResourceNotFoundError,
    StateTransitionError,
    IdempotencyConflictError,
)
from app.domain.enums import SessionState, UnitStatus, AuditAction, AttendanceStatus
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent
from app.schemas.attendance import AttendanceCommitRequest, CommitReceiptResponse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommitService:

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
        if session.state == SessionState.FINALIZED:
            raise StateTransitionError(
                message="Attendance for this session has already been finalized.",
                current_state=session.state.value,
                attempted_state="FINALIZED",
                reason_code="SESSION_ALREADY_FINALIZED",
            )

        if session.state != SessionState.IN_REVIEW:
            raise StateTransitionError(
                message=f"Session must be in IN_REVIEW state before attendance can be committed (current: {session.state.value}).",
                current_state=session.state.value,
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
        receipt_hash = hashlib.sha256(json.dumps(receipt_payload, sort_keys=True).encode()).hexdigest()

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
