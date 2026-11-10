"""
FRS V7.1 K² — Student Biometric Enrollment & Lifecycle Schemas.
Conforms to strict enrollment pipeline contracts.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.domain.enums import EnrollmentSubmissionStatus


class EnrollmentSubmissionCreate(BaseModel):
    roll_number: str = Field(..., min_length=3, max_length=50, description="Institutional Roll Number / Student ID")
    full_name: str = Field(..., min_length=2, max_length=100, description="Student Full Name")
    institutional_email: EmailStr = Field(..., description="Institutional Email Address")
    department: str = Field(..., min_length=2, max_length=100, description="Academic Department (e.g., CSE, ECE)")
    academic_year: str = Field(..., min_length=4, max_length=50, description="Academic Year / Batch (e.g., 2024-2028)")
    cohort_id: Optional[str] = Field(None, description="Optional Cohort UUID")
    consent_acknowledged: bool = Field(..., description="Explicit acknowledgement of biometric notice & voluntary consent")


class EnrollmentSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    roll_number: str
    full_name: str
    institutional_email: str
    department: str
    academic_year: str
    cohort_id: Optional[str] = None
    status: EnrollmentSubmissionStatus
    consent_acknowledged: bool
    rejection_reason: Optional[str] = None
    photo_sha256: str
    photo_storage_path: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class EnrollmentReviewActionRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection or targeted recapture guidance")


class RecentSessionItem(BaseModel):
    session_id: str
    subject_code: str
    subject_name: str
    cohort: str
    faculty: str
    conducted_units: int
    present_count: int
    total_enrolled: int
    attendance_percent: str
    receipt_hash: str
    timestamp: str


class AdminDashboardStatsResponse(BaseModel):
    total_enrolled_students: int
    total_active_offerings: int
    pending_submissions_count: int
    finalized_sessions_count: int
    conducted_units_today: int = 0
    active_departments_count: int = 0
    active_cohorts_count: int = 0
    recent_sessions: List[RecentSessionItem] = []
    system_readiness: str
