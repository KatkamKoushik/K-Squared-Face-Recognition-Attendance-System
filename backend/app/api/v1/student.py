"""
FRS V7.1 K² — Student Portal API Endpoints.
Guarantees strict tenant isolation: students can only query their own attendance
and submit appeals against their own records.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_correlation_id, require_roles
from app.core.database import get_db
from app.domain.enums import UserRole, AppealStatus
from app.domain.models.academic import User
from app.schemas.common import ResponseEnvelope
from app.schemas.attendance import AttendanceAppealCreate, AttendanceAppealResponse
from app.services.student_service import StudentService

router = APIRouter(prefix="/student", tags=["Student Portal & Attendance Dossier"])


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    roll_number: str
    full_name: str
    institutional_email: Optional[str] = None
    cohort_name: str
    department_name: str


class StudentAttendanceSummaryItem(BaseModel):
    offering_id: str
    subject_code: str
    subject_name: str
    section: str
    total_sessions: int
    eligible_conducted_units: int
    attended_conducted_units: int
    attendance_percent: Optional[float] = None
    eligibility_status: str


class AppealReviewRequest(BaseModel):
    approved: bool
    review_notes: str


@router.get("/me", response_model=ResponseEnvelope[StudentProfileResponse])
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Retrieves authoritative student profile for currently logged in student."""
    student = StudentService.get_student_for_user(db, current_user)
    data = StudentProfileResponse(
        id=student.id,
        roll_number=student.roll_number,
        full_name=student.full_name,
        institutional_email=student.institutional_email,
        cohort_name=student.cohort.name if student.cohort else "Assigned Cohort",
        department_name=student.cohort.department.name if student.cohort and student.cohort.department else "Department",
    )
    return ResponseEnvelope(data=data, correlation_id=correlation_id)


@router.get("/me/attendance", response_model=ResponseEnvelope[List[StudentAttendanceSummaryItem]])
def get_my_attendance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Calculates official attendance summary across all enrolled subjects for current student."""
    student = StudentService.get_student_for_user(db, current_user)
    summary = StudentService.get_attendance_summary(db, student)
    items = [StudentAttendanceSummaryItem(**s) for s in summary]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.get("/me/attendance/offerings/{offering_id}", response_model=ResponseEnvelope[Dict[str, Any]])
def get_my_offering_ledger(
    offering_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Granular unit-level attendance history for a single enrolled subject."""
    student = StudentService.get_student_for_user(db, current_user)
    ledger = StudentService.get_offering_ledger(db, student, offering_id)
    return ResponseEnvelope(data=ledger, correlation_id=correlation_id)


@router.post("/me/appeals", response_model=ResponseEnvelope[AttendanceAppealResponse], status_code=status.HTTP_201_CREATED)
def submit_my_appeal(
    data: AttendanceAppealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Submits a formal student attendance appeal for an absent session unit."""
    student = StudentService.get_student_for_user(db, current_user)
    appeal = StudentService.submit_appeal(db, student, data, correlation_id)
    return ResponseEnvelope(data=AttendanceAppealResponse.model_validate(appeal), correlation_id=correlation_id)


@router.get("/me/appeals", response_model=ResponseEnvelope[List[AttendanceAppealResponse]])
def list_my_appeals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Lists all appeals and review outcomes for the logged-in student."""
    student = StudentService.get_student_for_user(db, current_user)
    appeals = StudentService.list_student_appeals(db, student)
    items = [AttendanceAppealResponse.model_validate(a) for a in appeals]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.get("/appeals/all", response_model=ResponseEnvelope[List[AttendanceAppealResponse]])
def list_all_appeals_admin(
    status_filter: Optional[AppealStatus] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY, UserRole.SUB_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    """Administrative endpoint: lists student appeals, scoped by department for department admins."""
    appeals = StudentService.list_all_appeals(db, status=status_filter, limit=limit, user=current_user)
    items = [AttendanceAppealResponse.model_validate(a) for a in appeals]
    return ResponseEnvelope(data=items, correlation_id=correlation_id)


@router.post("/appeals/{appeal_id}/review", response_model=ResponseEnvelope[AttendanceAppealResponse])
def review_appeal_admin(
    appeal_id: str,
    req: AppealReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.FACULTY, UserRole.SUB_ADMIN])),
    correlation_id: str = Depends(get_correlation_id),
):
    """Administrative endpoint: approves or rejects a student attendance appeal."""
    appeal = StudentService.review_appeal(
        db=db,
        appeal_id=appeal_id,
        reviewer=current_user,
        approved=req.approved,
        review_notes=req.review_notes,
        correlation_id=correlation_id,
    )
    return ResponseEnvelope(data=AttendanceAppealResponse.model_validate(appeal), correlation_id=correlation_id)
