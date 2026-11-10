"""
FRS V7.1 K² — Atomic Attendance Commit & Institutional Analytics Endpoints.
"""

from fastapi import APIRouter, Depends, status, Response
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
    AttendanceCorrectionRequest,
    AttendanceCorrectionResponse,
    ReceiptVerificationResponse,
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


@router.post(
    "/sessions/{session_id}/receipt/verify",
    response_model=ResponseEnvelope[ReceiptVerificationResponse],
    status_code=status.HTTP_200_OK,
)
def verify_session_receipt(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Cryptographically verifies the authenticity and ledger consistency of a commit receipt.
    Recomputes HMAC signature and cross-checks actual database attendance records.
    Guarded by object-level authorization: caller must be conducting faculty or admin.
    """
    verification = CommitService.verify_session_receipt(
        db=db,
        session_id=session_id,
        user=current_user,
    )
    return ResponseEnvelope(data=verification, correlation_id=correlation_id)


@router.post(
    "/sessions/{session_id}/corrections",
    response_model=ResponseEnvelope[AttendanceCorrectionResponse],
    status_code=status.HTTP_200_OK,
)
def apply_attendance_correction(
    session_id: str,
    request: AttendanceCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Applies an audited post-commit attendance override or processes an official student appeal.
    Records an append-only AuditEvent and updates ledger statistics.
    Guarded by object-level authorization: caller must be conducting faculty or admin.
    """
    response = CommitService.apply_attendance_correction(
        db=db,
        session_id=session_id,
        user=current_user,
        request=request,
        correlation_id=correlation_id,
    )
    return ResponseEnvelope(data=response, correlation_id=correlation_id)


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


@router.get("/offerings/{offering_id}/export/csv")
def export_offering_attendance_csv(
    offering_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exports finalized attendance records for an academic offering formatted as CSV.
    Adheres strictly to the institutional denominator: attended_units / eligible_units.
    """
    import csv
    import io

    if current_user.role != UserRole.ADMIN:
        faculty = db.execute(
            select(Faculty).where(Faculty.user_id == current_user.id)
        ).scalar_one_or_none()
        if not faculty:
            raise PermissionDeniedError(
                message="User does not have an active faculty profile.",
                reason_code="FACULTY_PROFILE_NOT_FOUND",
            )
        AcademicService.verify_faculty_assignment(
            db=db,
            faculty_id=faculty.id,
            offering_id=offering_id,
        )

    analytics = AnalyticsService.get_offering_attendance_analytics(db, offering_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Roll Number",
        "Student Name",
        "Attended Units",
        "Conducted Units",
        "Attendance Percentage",
        "Institutional Status",
    ])

    for stat in analytics.student_stats:
        pct_str = f"{stat.attendance_percent:.2f}%" if stat.attendance_percent is not None else "N/A"
        status_label = "NOT_EVALUATED"
        if stat.attendance_percent is not None:
            if stat.attendance_percent >= 75.0:
                status_label = "ELIGIBLE"
            elif stat.attendance_percent >= 65.0:
                status_label = "CONDONATION_REQUIRED"
            else:
                status_label = "DETENTION_RISK"

        writer.writerow([
            stat.roll_number,
            stat.full_name,
            stat.attended_conducted_units,
            stat.eligible_conducted_units,
            pct_str,
            status_label,
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="attendance_{offering_id[:8]}.csv"'
        },
    )

