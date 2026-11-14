"""
K² FRS — Faculty Proposal Review Endpoints.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_faculty, get_current_user, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.enums import AttendanceStatus, AuditAction
from app.domain.models.academic import Faculty, User
from app.domain.models.audit import AuditEvent
from app.schemas.common import ResponseEnvelope
from app.schemas.review import SessionProposalReviewResponse
from app.services.review_service import ReviewService
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Faculty Review & Proposals"])


class CandidateAdjudicationItem(BaseModel):
    student_id: str
    status: AttendanceStatus
    reason: Optional[str] = "FACULTY_MANUAL_REVIEW"


class SessionAdjudicationRequest(BaseModel):
    adjudications: List[CandidateAdjudicationItem]


@router.get("/{session_id}/proposal", response_model=ResponseEnvelope[SessionProposalReviewResponse])
def get_session_proposal(
    session_id: str,
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Returns the evidence-based attendance proposal for faculty review.
    Reconciles multi-frame sightings against the frozen session roster.
    """
    session = SessionService.get_session_by_id(db, session_id)
    if session.faculty_id != faculty.id:
        raise PermissionDeniedError(
            message="You are not authorized to access proposals for this session.",
            reason_code="FACULTY_MISMATCH",
        )

    proposal = ReviewService.generate_session_proposal(db, session_id)
    return ResponseEnvelope(data=proposal, correlation_id=correlation_id)


@router.post("/{session_id}/adjudicate", response_model=ResponseEnvelope[Dict[str, Any]])
def adjudicate_session_proposal(
    session_id: str,
    request: SessionAdjudicationRequest,
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Records faculty manual adjudications and audit logs the review action.
    """
    session = SessionService.get_session_by_id(db, session_id)
    if session.faculty_id != faculty.id:
        raise PermissionDeniedError(
            message="You are not authorized to adjudicate proposals for this session.",
            reason_code="FACULTY_MISMATCH",
        )

    audit_ev = AuditEvent(
        session_id=session.id,
        actor_id=current_user.id,
        action=AuditAction.PROPOSAL_REVIEWED,
        reason=f"Faculty adjudicated {len(request.adjudications)} candidate proposal(s)",
        before_state={"session_id": session_id, "state": session.state.value if hasattr(session.state, 'value') else str(session.state)},
        after_state={"adjudications_count": len(request.adjudications)},
        correlation_id=correlation_id,
    )
    db.add(audit_ev)
    db.commit()

    return ResponseEnvelope(
        data={
            "session_id": session_id,
            "adjudications_applied": len(request.adjudications),
            "status": "ADJUDICATIONS_RECORDED",
        },
        correlation_id=correlation_id,
    )
