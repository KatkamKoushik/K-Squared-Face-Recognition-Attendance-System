"""
FRS V7.1 K² — Frame Upload & Face Evidence Schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.domain.enums import EvidenceState


class FrameUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: str
    frame_index: int
    content_sha256: str
    width: int
    height: int
    status: str
    received_at: datetime


class FaceEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    frame_id: str
    box_x1: float
    box_y1: float
    box_x2: float
    box_y2: float
    detection_score: float
    quality_score: float
    quality_reason: str
    candidate_student_id: Optional[str]
    similarity_score: Optional[float]
    score_margin: Optional[float]
    evidence_state: EvidenceState
    reason_code: str


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    created_at: datetime
    frames: List[FrameUploadResponse] = []
