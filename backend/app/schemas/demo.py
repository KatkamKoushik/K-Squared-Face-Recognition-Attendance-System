"""
FRS V7.1 K² — Demo Ground-Truth Visualizer DTO Schemas.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class DemoFaceBox(BaseModel):
    face_index: int
    box: Tuple[float, float, float, float] = Field(description="Normalized coordinates (x1, y1, x2, y2)")
    detection_score: float
    quality_score: float
    quality_reason: str
    face_crop_base64: str
    status: str  # MATCHED, UNKNOWN_VISITOR, AMBIGUOUS, QUALITY_REJECTED
    attendance_granted: bool
    student_id: Optional[str] = None
    roll_number: Optional[str] = None
    full_name: Optional[str] = None
    similarity_score: float = 0.0
    margin: float = 0.0
    reference_photo_base64: Optional[str] = None
    color_hex: str
    badge_label: str


class DemoStudentResult(BaseModel):
    student_id: str
    roll_number: str
    full_name: str
    attendance_granted: bool
    status: str  # PRESENT, ABSENT
    similarity_score: Optional[float] = None
    face_crop_base64: Optional[str] = None
    reference_photo_base64: Optional[str] = None


class DemoEnrolledStudentSummary(BaseModel):
    student_id: str
    roll_number: str
    full_name: str
    is_active: bool
    has_reference_photo: bool


class DemoAnalysisResponse(BaseModel):
    total_detected_faces: int
    total_enrolled_students: int
    present_count: int
    absent_count: int
    unknown_count: int
    detected_faces: List[DemoFaceBox]
    attendance_granted: List[DemoStudentResult]
    attendance_not_granted: List[DemoStudentResult]
    unidentified_faces: List[DemoFaceBox]

