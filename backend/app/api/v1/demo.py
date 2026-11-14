"""
K² FRS — Universal Demo Testing & Ground-Truth Visualizer API Router.
Provides open-access verification of YuNet face detection and SFace roster matching
with optional department filtering and resolution-adaptive thresholding.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_correlation_id, get_current_user, require_roles
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.enums import UserRole
from app.domain.models.academic import User
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
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.SUB_ADMIN, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.DEVELOPER])),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Returns the enrolled students with registered face profiles, optionally filtered by department.
    Requires authenticated institutional access (SEC-02).
    """
    is_authorized = True
    if current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
        if current_user.department:
            if department_code and department_code.strip().upper() not in (current_user.department.code.upper(), "ALL", ""):
                raise PermissionDeniedError(
                    message=f"Access denied: Department user is isolated to department '{current_user.department.code}'.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
            department_code = current_user.department.code

    students = DemoService.list_enrolled_demo_students(
        db, department_code=department_code, is_authorized=is_authorized
    )
    return ResponseEnvelope(data=students, correlation_id=correlation_id)


@router.post("/analyze", response_model=ResponseEnvelope[DemoAnalysisResponse])
async def analyze_demo_image(
    file: UploadFile = File(...),
    match_threshold: float = Form(0.363),
    margin_threshold: float = Form(0.10),
    blur_threshold: float = Form(25.0),
    department_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.SUB_ADMIN, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.DEVELOPER])),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Processes a group or individual classroom photograph for ground-truth inspection:
    - Normalizes EXIF orientation so pixel coordinates match visual displays.
    - Detects all faces using YuNet ONNX.
    - Applies resolution-adaptive cosine thresholding for distant/crowd faces.
    - Searches against enrolled student identities (optionally scoped to a department).
    - Enforces bipartite mutual exclusivity to eliminate duplicate identity collisions.
    - Requires authenticated institutional access (SEC-02).
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded photograph file is empty.",
        )

    try:
        is_authorized = True
        if current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
            if current_user.department:
                if department_code and department_code.strip().upper() not in (current_user.department.code.upper(), "ALL", ""):
                    raise PermissionDeniedError(
                        message=f"Access denied: Department user is isolated to department '{current_user.department.code}'.",
                        reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                    )
                department_code = current_user.department.code

        result = DemoService.analyze_demo_photo(
            db=db,
            image_bytes=file_bytes,
            match_threshold=match_threshold,
            margin_threshold=margin_threshold,
            blur_threshold=blur_threshold,
            department_code=department_code,
            is_authorized=is_authorized,
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
