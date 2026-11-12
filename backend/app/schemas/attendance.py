"""
K² FRS — Atomic Attendance Commit & Analytics Schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.domain.enums import AttendanceStatus, AppealStatus


class StudentUnitDecision(BaseModel):
    student_id: str
    unit_index: int = Field(..., ge=1, le=4)
    status: AttendanceStatus
    reason_code: str = Field(default="FACULTY_FINAL_COMMIT")
    source_evidence_id: Optional[str] = None


class AttendanceCommitRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=16, max_length=128, description="Cryptographic client idempotency key")
    conducted_unit_indices: List[int] = Field(..., min_length=1, max_length=4)
    decisions: List[StudentUnitDecision] = Field(..., min_length=1)

    @field_validator("conducted_unit_indices")
    @classmethod
    def validate_conducted_unit_indices(cls, v: List[int]) -> List[int]:
        if len(v) != len(set(v)):
            raise ValueError("conducted_unit_indices must not contain duplicate values.")
        for idx in v:
            if idx < 1 or idx > 4:
                raise ValueError(f"conducted_unit_index {idx} out of bounds: must be between 1 and 4.")
        return sorted(v)


class CommitReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    idempotency_key: str
    committed_by_user_id: str
    total_conducted_units: int
    total_present_records: int
    total_absent_records: int
    receipt_hash: str
    model_version: Optional[str] = None
    calibration_threshold: Optional[float] = None
    committed_at: datetime


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    unit_id: str
    student_id: str
    status: AttendanceStatus
    finalized_by_user_id: str
    reason_code: str
    committed_at: datetime


class StudentAttendanceStat(BaseModel):
    student_id: str
    roll_number: str
    full_name: str
    attended_conducted_units: int
    eligible_conducted_units: int
    attendance_percent: Optional[float] = None  # None if denominator is 0 (returns N/A)


class OfferingAttendanceAnalyticsResponse(BaseModel):
    offering_id: str
    total_sessions: int
    total_conducted_units: int
    student_stats: List[StudentAttendanceStat]


class AttendanceCorrectionRequest(BaseModel):
    student_id: str
    unit_index: int = Field(..., ge=1, le=4)
    new_status: AttendanceStatus
    action_type: str = Field(..., description="'OVERRIDE' for faculty correction, 'APPEAL' for student appeal")
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory institutional justification")
    reference_document: Optional[str] = Field(None, max_length=100, description="Medical cert / HOD memo ref")


class AttendanceCorrectionResponse(BaseModel):
    record_id: str
    session_id: str
    student_id: str
    unit_index: int
    previous_status: AttendanceStatus
    new_status: AttendanceStatus
    action: str
    audit_event_id: str
    updated_at: datetime


class ReceiptVerificationResponse(BaseModel):
    session_id: str
    receipt_id: str
    is_valid: bool
    signature_verified: bool
    ledger_records_matched: bool
    total_conducted_units: int
    total_present_records: int
    total_absent_records: int
    receipt_hash: str
    verified_at: datetime


class AttendanceAppealCreate(BaseModel):
    session_id: str
    unit_id: str
    reason: str = Field(..., min_length=5, max_length=500)
    evidence_path: Optional[str] = None


class AttendanceAppealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    session_id: str
    unit_id: str
    reason: str
    evidence_path: Optional[str] = None
    status: AppealStatus
    review_notes: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

