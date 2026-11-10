"""
FRS V7.1 K² — Session & Roster Snapshot DTO Schemas.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import SessionState, UnitStatus


class SessionCreateRequest(BaseModel):
    offering_id: str
    class_group_id: Optional[str] = None
    planned_units: int = Field(default=1, ge=1, le=4, description="Instructional units conducted (1-4)")
    session_date: Optional[date] = None


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    unit_index: int
    is_conducted: bool
    status: UnitStatus


class SnapshotStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: str
    roll_number: str
    full_name: str
    cohort_id: str


class RosterSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    snapshot_version: int
    total_eligible_students: int
    frozen_at: datetime
    students: List[SnapshotStudentResponse]


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    offering_id: str
    class_group_id: Optional[str]
    faculty_id: str
    session_date: date
    state: SessionState
    policy_version_id: str
    planned_units: int
    model_version: Optional[str] = None
    calibration_threshold: Optional[float] = None
    created_at: datetime
    finalized_at: Optional[datetime]
    units: List[UnitResponse] = []


class UnitConfirmationRequest(BaseModel):
    unit_index: int = Field(..., ge=1, le=4)
    is_conducted: bool
