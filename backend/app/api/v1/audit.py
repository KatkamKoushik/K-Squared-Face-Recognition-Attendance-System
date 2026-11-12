"""
FRS V7.1 K² — Audit Trail Query Endpoints.
Guarded by ADMIN and OPERATOR roles.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.api.dependencies import require_roles, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.enums import UserRole
from app.domain.models.academic import User, Subject, SubjectOffering
from app.domain.models.session import AttendanceSession
from app.domain.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get("/events", response_model=ResponseEnvelope[List[AuditEventResponse]])
def query_audit_events(
    session_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    """Queries append-only application audit events with role and department isolation."""
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc())

    if current_user.role == UserRole.ADMIN:
        if not current_user.department_id:
            raise PermissionDeniedError(
                message="Department administrator has no assigned department.",
                reason_code="DEPARTMENT_ACCESS_RESTRICTED",
            )
        dept_user_ids = select(User.id).where(User.department_id == current_user.department_id)
        dept_session_ids = (
            select(AttendanceSession.id)
            .join(SubjectOffering, AttendanceSession.offering_id == SubjectOffering.id)
            .join(Subject, SubjectOffering.subject_id == Subject.id)
            .where(Subject.department_id == current_user.department_id)
        )
        stmt = stmt.where(
            or_(
                AuditEvent.actor_id.in_(dept_user_ids),
                AuditEvent.session_id.in_(dept_session_ids),
            )
        )

    if session_id:
        stmt = stmt.where(AuditEvent.session_id == session_id)
    if actor_id:
        stmt = stmt.where(AuditEvent.actor_id == actor_id)

    stmt = stmt.limit(limit)
    events = list(db.execute(stmt).scalars().all())
    items = [AuditEventResponse.model_validate(e) for e in events]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)
