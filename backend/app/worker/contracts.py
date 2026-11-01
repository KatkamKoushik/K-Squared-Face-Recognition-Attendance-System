"""
FRS V7.1 K² — Model-Neutral Typed Vision Contracts.
Decouples inference implementations from database models and business logic.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    box: Tuple[float, float, float, float] = Field(description="Normalized coordinates (x1, y1, x2, y2) in range [0, 1]")
    score: float
    landmarks: Optional[List[Tuple[float, float]]] = None
    detector_model_hash: str


class QualityResult(BaseModel):
    score: float = Field(description="Per-face quality score [0.0 - 1.0]")
    is_usable: bool
    reason_code: str  # e.g., "SHARP", "BLURRY", "OCCLUDED", "EXTREME_YAW"


class EmbeddingResult(BaseModel):
    vector: List[float]
    dimension: int = 512
    namespace: str = "arcface_r50_512d_v1"
    recognizer_model_hash: str


class RetrievalCandidate(BaseModel):
    student_id: str
    similarity_score: float
    margin_to_second: float
    is_matched: bool
    reason_code: str


class SecurityResult(BaseModel):
    is_live: bool
    score: float
    status: str  # "PASS", "FAIL", "UNCERTAIN", "SKIPPED"
    reason_code: str
