"""
FRS V7.1 K² — Data Governance, Biometric Privacy & Retention Schemas.
Enforces institutional consent, non-biometric alternatives, and ephemeral storage purging.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PurgeRequest(BaseModel):
    retention_days: int = Field(default=7, ge=0, le=365, description="Purge frames older than this many days post-finalization")
    session_id: Optional[str] = Field(None, description="Optional specific session ID to immediately purge")


class PurgeResponse(BaseModel):
    purged_frames_count: int
    freed_bytes: int
    retention_days: int
    audit_event_id: str
    executed_at: datetime


class StudentConsentStatus(BaseModel):
    student_id: str
    roll_number: str
    full_name: str
    biometric_consent_active: bool
    profile_version: Optional[int] = None
    embedding_namespace: Optional[str] = None
    alternative_roll_call_required: bool


class ConsentToggleRequest(BaseModel):
    student_id: str
    consent_active: bool
    reason: str = Field(..., min_length=5, max_length=255, description="Institutional justification for consent change")


class GovernanceSummaryResponse(BaseModel):
    total_students: int
    students_with_biometric_consent: int
    students_withheld_consent: int
    consent_compliance_percentage: float
    total_captured_frames: int
    active_unpurged_frames: int
    purged_frames: int
    disk_usage_bytes: int
    disk_usage_mb: float
    retention_policy_days: int
