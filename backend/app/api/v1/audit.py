"""
FRS V7.1 K² — Audit Trail Query Endpoints.
Guarded by ADMIN and OPERATOR roles.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.api.dependencies import require_roles, get_correlation_id
from app.core.database import get_db
from app.domain.enums import UserRole
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
    admin_user=Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
    correlation_id: str = Depends(get_correlation_id),
):
    """Queries append-only application audit events with resource filtering."""
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit)
    if session_id:
        stmt = stmt.where(AuditEvent.session_id == session_id)
    if actor_id:
        stmt = stmt.where(AuditEvent.actor_id == actor_id)

    events = list(db.execute(stmt).scalars().all())
    items = [AuditEventResponse.model_validate(e) for e in events]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)
