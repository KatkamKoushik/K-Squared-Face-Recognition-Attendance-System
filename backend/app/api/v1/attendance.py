"""
FRS V7.1 K² — Atomic Attendance Commit & Institutional Analytics Endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_current_faculty, get_correlation_id
from app.core.database import get_db
from app.domain.models.academic import User, Faculty
from app.schemas.attendance import (
    AttendanceCommitRequest,
    CommitReceiptResponse,
    OfferingAttendanceAnalyticsResponse,
)
from app.schemas.common import ResponseEnvelope
from app.services.commit_service import CommitService
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Attendance Ledger & Analytics"])


@router.post(
    "/sessions/{session_id}/commit",
    response_model=ResponseEnvelope[CommitReceiptResponse],
    status_code=status.HTTP_200_OK,
)
def commit_attendance(
    session_id: str,
    request: AttendanceCommitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Commits final attendance inside an atomic ACID transaction.
    Returns a cryptographically signed durable receipt with replay idempotency.
    """
    receipt = CommitService.commit_session_attendance(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        faculty_id=faculty.id,
        request=request,
        correlation_id=correlation_id,
    )
    return ResponseEnvelope(data=CommitReceiptResponse.model_validate(receipt), correlation_id=correlation_id)


@router.get(
    "/offerings/{offering_id}/analytics",
    response_model=ResponseEnvelope[OfferingAttendanceAnalyticsResponse],
)
def get_offering_analytics(
    offering_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Calculates institutional attendance arithmetic from committed student-unit records.
    Denominator rule: attended_conducted_units / eligible_conducted_units.
    """
    analytics = AnalyticsService.get_offering_attendance_analytics(db, offering_id)
    return ResponseEnvelope(data=analytics, correlation_id=correlation_id)
