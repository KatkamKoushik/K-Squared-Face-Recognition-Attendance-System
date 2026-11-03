"""
FRS V7.1 K² — Atomic Attendance Commit & Analytics Schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import AttendanceStatus


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
