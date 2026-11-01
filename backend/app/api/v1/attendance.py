"""
FRS V7.1 K² — Atomic Attendance Commit & Institutional Analytics Endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_current_faculty, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.enums import UserRole
from app.domain.models.academic import User, Faculty
from app.schemas.attendance import (
    AttendanceCommitRequest,
    CommitReceiptResponse,
    OfferingAttendanceAnalyticsResponse,
)
from app.schemas.common import ResponseEnvelope
from app.services.commit_service import CommitService
from app.services.analytics_service import AnalyticsService
from app.services.academic_service import AcademicService

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
    "/sessions/{session_id}/receipt",
    response_model=ResponseEnvelope[CommitReceiptResponse],
)
def get_session_receipt(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Retrieves the authoritative commit receipt for a finalized attendance session.
    Guarded by object-level authorization: caller must be conducting faculty or admin.
    """
    receipt = CommitService.get_session_receipt(
        db=db,
        session_id=session_id,
        user=current_user,
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
    Guarded by object-level authorization: Admins have institutional scope, faculty
    must hold an active FacultyAssignment for the requested offering.
    """
    if current_user.role != UserRole.ADMIN:
        faculty = db.execute(
            select(Faculty).where(Faculty.user_id == current_user.id)
        ).scalar_one_or_none()
        if not faculty:
            raise PermissionDeniedError(
                message="User does not have an active faculty profile.",
                reason_code="FACULTY_PROFILE_NOT_FOUND",
            )
        # Verify faculty assignment
        AcademicService.verify_faculty_assignment(
            db=db,
            faculty_id=faculty.id,
            offering_id=offering_id,
        )

    analytics = AnalyticsService.get_offering_attendance_analytics(db, offering_id)
    return ResponseEnvelope(data=analytics, correlation_id=correlation_id)
