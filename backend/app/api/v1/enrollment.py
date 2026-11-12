"""
FRS V7.1 K² — Student Enrollment & Admin Lifecycle Endpoints.
Public route for student selfie registration + protected admin routes for verification & approval.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, get_optional_current_user, require_roles, get_correlation_id
from app.core.errors import PermissionDeniedError
from app.domain.enums import UserRole, EnrollmentSubmissionStatus
from app.domain.models.academic import User, Department
from app.domain.models.student import EnrollmentSubmission
from app.schemas.common import ResponseEnvelope
from app.schemas.enrollment import (
    EnrollmentSubmissionCreate,
    EnrollmentSubmissionResponse,
    EnrollmentReviewActionRequest,
    AdminDashboardStatsResponse,
)
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/enrollment", tags=["Student Biometric Enrollment & Lifecycle"])


def _check_submission_department_access(db: Session, sub: EnrollmentSubmission, current_user: User) -> None:
    """Enforces strict department isolation on student enrollment review operations."""
    if current_user.role in (UserRole.SUPER_ADMIN, UserRole.DEVELOPER):
        return
    if current_user.role in (UserRole.ADMIN, UserRole.FACULTY, UserRole.SUB_ADMIN):
        if not current_user.department_id:
            raise PermissionDeniedError(
                message="Access denied: Administrator has no assigned department.",
                reason_code="DEPARTMENT_ACCESS_RESTRICTED",
            )
        dept = db.get(Department, current_user.department_id)
        dept_code = dept.code.upper() if dept else ""
        sub_dept = (sub.department or "").upper()
        is_same_dept = (sub_dept == dept_code) or (sub.cohort is not None and sub.cohort.department_id == current_user.department_id)
        if not is_same_dept:
            raise PermissionDeniedError(
                message="Access denied: Cannot review or modify enrollment submissions from another department.",
                reason_code="DEPARTMENT_ACCESS_RESTRICTED",
            )


@router.post("/submit", response_model=ResponseEnvelope[EnrollmentSubmissionResponse], status_code=status.HTTP_201_CREATED)
async def submit_student_enrollment(
    roll_number: str = Form(...),
    full_name: str = Form(...),
    institutional_email: str = Form(...),
    department: str = Form(...),
    academic_year: str = Form(...),
    cohort_id: Optional[str] = Form(None),
    consent_acknowledged: bool = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Public student endpoint: submits details and portrait for biometric attendance enrollment.
    Enforces format decoding, EXIF stripping, and YuNet face verification before staging in review queue.
    """
    file_bytes = await photo.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded photograph file is empty.",
        )

    create_data = EnrollmentSubmissionCreate(
        roll_number=roll_number,
        full_name=full_name,
        institutional_email=institutional_email,
        department=department,
        academic_year=academic_year,
        cohort_id=cohort_id,
        consent_acknowledged=consent_acknowledged,
    )

    try:
        sub = EnrollmentService.submit_enrollment(
            db=db,
            data=create_data,
            file_bytes=file_bytes,
            mime_type=photo.content_type or "image/jpeg",
        )
        return ResponseEnvelope(
            data=EnrollmentSubmissionResponse.model_validate(sub),
            correlation_id=correlation_id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve)) from ve


@router.get("/submissions", response_model=ResponseEnvelope[List[EnrollmentSubmissionResponse]])
def list_enrollment_submissions(
    status_filter: Optional[EnrollmentSubmissionStatus] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    """Admin endpoint: lists student enrollment submissions scoped to administrator's department."""
    dept_id = None
    dept_code = None
    if current_user.role == UserRole.ADMIN:
        if not current_user.department_id:
            raise PermissionDeniedError(
                message="Department administrator has no assigned department.",
                reason_code="DEPARTMENT_ACCESS_RESTRICTED",
            )
        dept_id = current_user.department_id
        dept = db.get(Department, dept_id)
        dept_code = dept.code if dept else None

    subs = EnrollmentService.list_submissions(
        db=db,
        status=status_filter,
        search=search,
        limit=limit,
        offset=offset,
        department_code=dept_code,
        department_id=dept_id,
    )
    items = [EnrollmentSubmissionResponse.model_validate(s) for s in subs]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.get("/submissions/{submission_id}", response_model=ResponseEnvelope[EnrollmentSubmissionResponse])
def get_enrollment_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    sub = EnrollmentService.get_submission_by_id(db, submission_id)
    _check_submission_department_access(db, sub, current_user)
    return ResponseEnvelope(data=EnrollmentSubmissionResponse.model_validate(sub), correlation_id=correlation_id)


@router.get("/submissions/{submission_id}/photo")
def get_submission_photo(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY])),
):
    """Protected endpoint: securely serves the private enrollment photograph for authorized verification."""
    sub = EnrollmentService.get_submission_by_id(db, submission_id)
    _check_submission_department_access(db, sub, current_user)

    if sub.photo_storage_path and (sub.photo_storage_path.startswith("http://") or sub.photo_storage_path.startswith("https://")):
        return RedirectResponse(url=sub.photo_storage_path, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    photo_path = Path(sub.photo_storage_path)
    if not photo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo file not found on disk.")
    return FileResponse(
        path=photo_path,
        media_type=sub.photo_mime or "image/jpeg",
        filename=f"{sub.roll_number}_portrait.jpg",
    )


@router.post("/submissions/{submission_id}/approve", response_model=ResponseEnvelope[EnrollmentSubmissionResponse])
def approve_enrollment_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Admin endpoint: approves student enrollment within administrator's authorized department.
    Executes SFace 5-landmark embedding generation and promotes template to gallery.
    """
    sub = EnrollmentService.get_submission_by_id(db, submission_id)
    _check_submission_department_access(db, sub, current_user)

    try:
        sub = EnrollmentService.approve_submission(db, submission_id, admin_user_id=current_user.id)
        return ResponseEnvelope(data=EnrollmentSubmissionResponse.model_validate(sub), correlation_id=correlation_id)
    except PermissionDeniedError:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/submissions/{submission_id}/reject", response_model=ResponseEnvelope[EnrollmentSubmissionResponse])
def reject_enrollment_submission(
    submission_id: str,
    req: EnrollmentReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    sub = EnrollmentService.get_submission_by_id(db, submission_id)
    _check_submission_department_access(db, sub, current_user)

    sub = EnrollmentService.reject_submission(
        db, submission_id, admin_user_id=current_user.id, reason=req.reason or ""
    )
    return ResponseEnvelope(data=EnrollmentSubmissionResponse.model_validate(sub), correlation_id=correlation_id)


@router.post("/submissions/{submission_id}/recapture", response_model=ResponseEnvelope[EnrollmentSubmissionResponse])
def request_enrollment_recapture(
    submission_id: str,
    req: EnrollmentReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    sub = EnrollmentService.get_submission_by_id(db, submission_id)
    _check_submission_department_access(db, sub, current_user)

    sub = EnrollmentService.request_recapture(
        db, submission_id, admin_user_id=current_user.id, reason=req.reason or ""
    )
    return ResponseEnvelope(data=EnrollmentSubmissionResponse.model_validate(sub), correlation_id=correlation_id)


@router.get("/dashboard/stats", response_model=ResponseEnvelope[AdminDashboardStatsResponse])
def get_admin_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    """Admin endpoint: returns real live PostgreSQL database statistics, scoped by department for ADMIN."""
    dept_id = current_user.department_id if current_user.role == UserRole.ADMIN else None
    if current_user.role == UserRole.ADMIN and not dept_id:
        raise PermissionDeniedError(
            message="Department administrator has no assigned department.",
            reason_code="DEPARTMENT_ACCESS_RESTRICTED",
        )
    stats = EnrollmentService.get_dashboard_stats(db, department_id=dept_id)
    return ResponseEnvelope(data=AdminDashboardStatsResponse(**stats), correlation_id=correlation_id)
