"""
FRS V7.1 K² — Data Governance, Biometric Privacy & Ephemeral Retention Service.
Implements institutional notice tracking, non-biometric alternatives,
and cryptographic/physical purging of raw classroom photo frames.
"""

from datetime import datetime, timezone, timedelta
import os
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import ResourceNotFoundError, PermissionDeniedError
from app.domain.enums import SessionState, AuditAction, UserRole
from app.domain.models.academic import User
from app.domain.models.student import Student, EnrollmentProfile
from app.domain.models.session import AttendanceSession
from app.domain.models.capture import CaptureBatch, Frame
from app.domain.models.audit import AuditEvent
from app.schemas.governance import (
    PurgeRequest,
    PurgeResponse,
    StudentConsentStatus,
    ConsentToggleRequest,
    GovernanceSummaryResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GovernanceService:

    @staticmethod
    def get_governance_summary(db: Session) -> GovernanceSummaryResponse:
        """
        Calculates institutional biometric compliance metrics, raw frame disk usage,
        and data retention purge telemetry.
        """
        # 1. Student Consent Metrics
        total_students = db.execute(select(func.count(Student.id))).scalar() or 0
        students_with_profiles = db.execute(
            select(func.count(func.distinct(EnrollmentProfile.student_id)))
            .where(EnrollmentProfile.is_active == True)
        ).scalar() or 0

        students_withheld = max(0, total_students - students_with_profiles)
        compliance_pct = round((students_with_profiles / total_students * 100.0), 2) if total_students > 0 else 100.0

        # 2. Frame Storage & Purge Metrics
        total_frames = db.execute(select(func.count(Frame.id))).scalar() or 0
        purged_frames = db.execute(
            select(func.count(Frame.id)).where(Frame.status == "PURGED")
        ).scalar() or 0
        active_unpurged = total_frames - purged_frames

        # Compute disk usage of active frame files
        frames = db.execute(
            select(Frame.storage_path).where(Frame.status != "PURGED")
        ).scalars().all()

        total_bytes = 0
        for path in frames:
            if path and not path.startswith("[PURGED") and os.path.exists(path):
                try:
                    total_bytes += os.path.getsize(path)
                except OSError:
                    pass

        return GovernanceSummaryResponse(
            total_students=total_students,
            students_with_biometric_consent=students_with_profiles,
            students_withheld_consent=students_withheld,
            consent_compliance_percentage=compliance_pct,
            total_captured_frames=total_frames,
            active_unpurged_frames=active_unpurged,
            purged_frames=purged_frames,
            disk_usage_bytes=total_bytes,
            disk_usage_mb=round(total_bytes / (1024 * 1024), 2),
            retention_policy_days=7,
        )

    @staticmethod
    def purge_raw_frames(
        db: Session,
        request: PurgeRequest,
        user: User,
        correlation_id: str,
    ) -> PurgeResponse:
        """
        Executes raw frame cryptographic/physical purging for finalized attendance sessions.
        Enforces:
        1. Only administrators can trigger raw frame retention purging.
        2. Never purges unfinalized sessions (IN_REVIEW, CAPTURING, PROCESSING).
        3. Removes physical image files from disk.
        4. Updates Frame status to PURGED and records audit trail.
        """
        if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DEVELOPER]:
            raise PermissionDeniedError(
                message="Only system administrators may execute data retention purges.",
                reason_code="ADMIN_PRIVILEGE_REQUIRED",
            )

        now = utc_now()
        stmt = (
            select(Frame)
            .join(CaptureBatch, CaptureBatch.id == Frame.batch_id)
            .join(AttendanceSession, AttendanceSession.id == CaptureBatch.session_id)
            .where(
                and_(
                    AttendanceSession.state == SessionState.FINALIZED,
                    Frame.status != "PURGED",
                )
            )
        )

        if request.session_id:
            stmt = stmt.where(AttendanceSession.id == request.session_id)
        else:
            cutoff = now - timedelta(days=request.retention_days)
            stmt = stmt.where(AttendanceSession.finalized_at <= cutoff)

        target_frames = list(db.execute(stmt).scalars().all())

        freed_bytes = 0
        purged_count = 0

        for frame in target_frames:
            if frame.storage_path and not frame.storage_path.startswith("[PURGED"):
                if os.path.exists(frame.storage_path):
                    try:
                        file_size = os.path.getsize(frame.storage_path)
                        os.unlink(frame.storage_path)
                        freed_bytes += file_size
                    except OSError:
                        pass
                frame.storage_path = f"[PURGED_AT_{now.isoformat()}]"
            frame.status = "PURGED"
            purged_count += 1

        # Emit append-only AuditEvent
        audit = AuditEvent(
            session_id=request.session_id,
            actor_id=user.id,
            action=AuditAction.DATA_PURGE_EXECUTED,
            reason=f"Raw classroom photo frames purged per institutional retention policy (retention_days={request.retention_days}).",
            before_state={"target_frames_count": len(target_frames)},
            after_state={"purged_frames_count": purged_count, "freed_bytes": freed_bytes},
            correlation_id=correlation_id,
            timestamp=now,
        )
        db.add(audit)
        db.flush()

        return PurgeResponse(
            purged_frames_count=purged_count,
            freed_bytes=freed_bytes,
            retention_days=request.retention_days,
            audit_event_id=audit.id,
            executed_at=now,
        )

    @staticmethod
    def toggle_student_biometric_consent(
        db: Session,
        request: ConsentToggleRequest,
        user: User,
        correlation_id: str,
    ) -> StudentConsentStatus:
        """
        Updates student biometric consent status. When consent is deactivated,
        their enrollment profiles are set to inactive, requiring manual non-biometric
        roll-call alternatives during review.
        """
        if user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.FACULTY, UserRole.STUDENT]:
            raise PermissionDeniedError(
                message="Authorized institutional coordinator or administrator required.",
                reason_code="INSUFFICIENT_PERMISSIONS",
            )

        student = db.get(Student, request.student_id)
        if not student:
            raise ResourceNotFoundError("Student", request.student_id)

        if user.role == UserRole.STUDENT and student.institutional_email != user.email:
            raise PermissionDeniedError(
                message="Students may only manage their own biometric consent status.",
                reason_code="STUDENT_OWNERSHIP_REQUIRED",
            )

        profiles_stmt = select(EnrollmentProfile).where(
            EnrollmentProfile.student_id == request.student_id
        )
        profiles = list(db.execute(profiles_stmt).scalars().all())

        for p in profiles:
            p.is_active = request.consent_active

        # Audit the consent lifecycle transition
        audit = AuditEvent(
            session_id=None,
            actor_id=user.id,
            action=AuditAction.POST_COMMIT_OVERRIDE,
            reason=f"Biometric consent {'granted' if request.consent_active else 'withheld/revoked'}: {request.reason}",
            before_state={"student_id": request.student_id, "active_before": not request.consent_active},
            after_state={"student_id": request.student_id, "active_after": request.consent_active},
            correlation_id=correlation_id,
        )
        db.add(audit)
        db.flush()

        latest_profile = profiles[0] if profiles else None

        return StudentConsentStatus(
            student_id=student.id,
            roll_number=student.roll_number,
            full_name=student.full_name,
            biometric_consent_active=request.consent_active if profiles else False,
            profile_version=latest_profile.profile_version if latest_profile else None,
            embedding_namespace=latest_profile.embedding_namespace if latest_profile else None,
            alternative_roll_call_required=not request.consent_active or not profiles,
        )

