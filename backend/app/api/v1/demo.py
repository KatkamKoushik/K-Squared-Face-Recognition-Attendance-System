"""
FRS V7.1 K² — Universal Demo Testing & Ground-Truth Visualizer API Router.
Provides open-access verification of YuNet face detection and SFace roster matching
with optional department filtering and resolution-adaptive thresholding.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_correlation_id
from app.core.database import get_db
from app.schemas.common import ResponseEnvelope
from app.schemas.demo import (
    DemoAnalysisResponse,
    DemoEnrolledStudentSummary,
)
from app.services.demo_service import DemoService

router = APIRouter(prefix="/demo", tags=["Universal Demo Testing"])


@router.get("/enrolled-students", response_model=ResponseEnvelope[List[DemoEnrolledStudentSummary]])
def list_demo_students(
    department_code: Optional[str] = None,
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Returns the enrolled students with registered face profiles, optionally filtered by department.
    """
    students = DemoService.list_enrolled_demo_students(db, department_code=department_code)
    return ResponseEnvelope(data=students, correlation_id=correlation_id)


@router.post("/analyze", response_model=ResponseEnvelope[DemoAnalysisResponse])
async def analyze_demo_image(
    file: UploadFile = File(...),
    match_threshold: float = Form(0.460),
    margin_threshold: float = Form(0.10),
    blur_threshold: float = Form(50.0),
    department_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Processes a group or individual classroom photograph for ground-truth inspection:
    - Normalizes EXIF orientation so pixel coordinates match visual displays.
    - Detects all faces using YuNet ONNX.
    - Applies resolution-adaptive cosine thresholding for distant/crowd faces.
    - Searches against enrolled student identities (optionally scoped to a department).
    - Enforces bipartite mutual exclusivity to eliminate duplicate identity collisions.
    - Returns normalized bounding boxes, face crops, and attendance reconciliation.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded photograph file is empty.",
        )

    try:
        result = DemoService.analyze_demo_photo(
            db=db,
            image_bytes=file_bytes,
            match_threshold=match_threshold,
            margin_threshold=margin_threshold,
            blur_threshold=blur_threshold,
            department_code=department_code,
        )
        return ResponseEnvelope(data=result, correlation_id=correlation_id)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        ) from ve
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {exc}",
        ) from exc
