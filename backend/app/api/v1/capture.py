"""
K² FRS — Classroom Image Frame Capture Ingress Endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_faculty, get_correlation_id
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.models.academic import Faculty
from app.schemas.capture import FrameUploadResponse
from app.schemas.common import ResponseEnvelope
from app.services.ingress_service import IngressService
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Photo Ingress & Batches"])


@router.post(
    "/{session_id}/batches/{batch_id}/frames",
    response_model=ResponseEnvelope[FrameUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/{session_id}/frames",
    response_model=ResponseEnvelope[FrameUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
def upload_frame(
    session_id: str,
    batch_id: str = "default-batch",
    frame_index: int = Form(0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    faculty: Faculty = Depends(get_current_faculty),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Ingests and validates a classroom capture photo frame.
    Validates decode, byte size, strips EXIF, computes SHA-256, and enqueues bounded vision job.
    """
    session = SessionService.get_session_by_id(db, session_id)
    if session.faculty_id != faculty.id:
        raise PermissionDeniedError(
            message="You are not authorized to upload capture frames for this session.",
            reason_code="FACULTY_MISMATCH",
        )

    raw_bytes = file.file.read()
    frame = IngressService.process_frame_upload(
        db=db,
        session_id=session_id,
        batch_id=batch_id,
        frame_index=frame_index,
        raw_bytes=raw_bytes,
        correlation_id=correlation_id,
    )
    return ResponseEnvelope(data=FrameUploadResponse.model_validate(frame), correlation_id=correlation_id)
