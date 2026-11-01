"""
FRS V7.1 K² — Faculty Proposal Review & Uncertainty Schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from app.domain.enums import EvidenceState, AttendanceStatus


class CandidateProposalItem(BaseModel):
    student_id: str
    roll_number: str
    full_name: str
    proposal_status: Optional[AttendanceStatus] = None
    evidence_state: EvidenceState
    highest_similarity_score: Optional[float] = None
    sightings_count: int = 0
    requires_manual_attention: bool = False
    uncertainty_reason: Optional[str] = None


class UnknownFaceItem(BaseModel):
    evidence_id: str
    frame_id: str
    box_x1: float
    box_y1: float
    box_x2: float
    box_y2: float
    quality_score: float
    reason: str


class RecaptureHint(BaseModel):
    frame_id: str
    issue: str  # e.g., "LOW_LIGHTING", "BLURRY", "EXTREME_ANGLE"
    recommendation: str


class SessionProposalReviewResponse(BaseModel):
    session_id: str
    total_eligible_students: int
    proposed_present_count: int
    proposed_absent_count: int
    uncertain_count: int
    unknown_faces_count: int
    candidates: List[CandidateProposalItem]
    unknown_faces: List[UnknownFaceItem] = []
    recapture_hints: List[RecaptureHint] = []


class ManualReviewDecision(BaseModel):
    student_id: str
    unit_index: int = Field(default=1, ge=1, le=4)
    status: AttendanceStatus
    reason: str = Field(default="FACULTY_MANUAL_ADJUDICATION", max_length=100)
