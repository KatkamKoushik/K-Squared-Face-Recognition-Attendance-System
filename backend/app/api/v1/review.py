"""
FRS V7.1 K² — Faculty Proposal Review Endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_faculty, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.models.academic import Faculty
from app.schemas.common import ResponseEnvelope
from app.schemas.review import SessionProposalReviewResponse
from app.services.review_service import ReviewService
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Faculty Review & Proposals"])


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
