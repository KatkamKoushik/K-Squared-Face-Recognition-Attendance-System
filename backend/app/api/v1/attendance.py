"""
K² FRS — Atomic Attendance Commit & Institutional Analytics Endpoints.
"""

from fastapi import APIRouter, Depends, status, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.dependencies import get_current_user, get_current_faculty, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.domain.enums import UserRole
from app.domain.models.academic import User, Faculty, SubjectOffering
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


def _verify_offering_access(db: Session, current_user: User, offering_id: str) -> SubjectOffering:
    """
    Verifies offering access with strict department isolation for administrators
    and active faculty assignments for teaching faculty.
    """
    offering = db.execute(
        select(SubjectOffering)
        .options(selectinload(SubjectOffering.subject))
        .where(SubjectOffering.id == offering_id)
    ).scalar_one_or_none()
    if not offering:
        raise ResourceNotFoundError(resource="SubjectOffering", identifier=offering_id)

    # DEVELOPER and SUPER_ADMIN have campus-wide institutional access
    if current_user.role in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN):
        return offering

    # Department-scoped administrators (ADMIN and SUB_ADMIN)
    if current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
        offering_dept_id = offering.subject.department_id if offering.subject else None
        if not current_user.department_id or current_user.department_id != offering_dept_id:
            raise PermissionDeniedError(
                message=f"Access denied: Department administrator is isolated to department '{current_user.department_id}' and cannot access offerings of department '{offering_dept_id}'.",
                reason_code="DEPARTMENT_ACCESS_RESTRICTED",
            )
        return offering

    # Faculty members must hold an active assignment for the requested offering
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
    return offering


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
    Guarded by department-scoped authorization for admins and assignment checks for faculty.
    """
    _verify_offering_access(db=db, current_user=current_user, offering_id=offering_id)

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

    _verify_offering_access(db=db, current_user=current_user, offering_id=offering_id)

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


@router.get("/offerings/{offering_id}/export/xlsx")
def export_offering_attendance_xlsx(
    offering_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exports finalized attendance records for an academic offering formatted as Excel (.xlsx).
    Contains:
    - Tab 1: 'Attendance Summary' with student roll, name, units, percentage, status.
    - Tab 2: 'Session Audit Trail' with session ID, date, conducted units, receipt hash.
    Adheres strictly to the institutional denominator: attended_units / eligible_units.
    """
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from app.domain.models.session import AttendanceSession
    from app.domain.models.audit import CommitReceipt

    _verify_offering_access(db=db, current_user=current_user, offering_id=offering_id)

    analytics = AnalyticsService.get_offering_attendance_analytics(db, offering_id)

    wb = openpyxl.Workbook()

    # Sheet 1: Attendance Summary
    ws_summary = wb.active
    ws_summary.title = "Attendance Summary"

    headers = [
        "Roll Number",
        "Student Name",
        "Attended Units",
        "Conducted Units",
        "Attendance Percentage",
        "Institutional Status",
    ]
    ws_summary.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws_summary.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

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

        row = [
            stat.roll_number,
            stat.full_name,
            stat.attended_conducted_units,
            stat.eligible_conducted_units,
            pct_str,
            status_label,
        ]
        ws_summary.append(row)

    # Format data rows
    for row in ws_summary.iter_rows(min_row=2, max_row=ws_summary.max_row, min_col=1, max_col=6):
        for cell in row:
            cell.border = thin_border

    # Sheet 2: Session Metadata & Receipts
    ws_sessions = wb.create_sheet(title="Session Audit Trail")
    session_headers = [
        "Session ID",
        "Session Date",
        "State",
        "Planned Units",
        "Conducted Units",
        "Receipt Hash",
    ]
    ws_sessions.append(session_headers)
    for col_idx in range(1, len(session_headers) + 1):
        cell = ws_sessions.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    sessions = db.execute(
        select(AttendanceSession)
        .where(AttendanceSession.offering_id == offering_id)
        .order_by(AttendanceSession.session_date.desc())
    ).scalars().all()

    for s in sessions:
        conducted_count = sum(1 for u in s.units if u.is_conducted) if s.units else 0
        receipt = db.execute(
            select(CommitReceipt).where(CommitReceipt.session_id == s.id)
        ).scalar_one_or_none()
        receipt_hash = receipt.receipt_hash if receipt else "N/A"

        state_str = s.state.value if hasattr(s.state, "value") else str(s.state)
        ws_sessions.append([
            s.id,
            s.session_date.isoformat(),
            state_str,
            s.planned_units,
            conducted_count,
            receipt_hash,
        ])

    for row in ws_sessions.iter_rows(min_row=2, max_row=ws_sessions.max_row, min_col=1, max_col=6):
        for cell in row:
            cell.border = thin_border

    # Auto-adjust column widths
    for ws in [ws_summary, ws_sessions]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="attendance_{offering_id[:8]}.xlsx"'
        },
    )

