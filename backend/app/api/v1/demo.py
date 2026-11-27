"""
K² FRS — Universal Demo Testing API Endpoints.
Provides ground-truth visualizer endpoints for branch-agnostic evaluation,
enforcing privacy sanitization and role-scoped permissions.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_correlation_id, get_optional_current_user
from app.core.database import get_db
from app.core.errors import PermissionDeniedError
from app.domain.enums import UserRole
from app.domain.models.academic import User
from app.schemas.common import ResponseEnvelope
from app.schemas.demo import (
    DemoAnalysisResponse,
    DemoEnrolledStudentSummary,
    DemoModelsResponse,
    DemoSelectModelRequest,
)
from app.services.demo_service import DemoService

router = APIRouter(prefix="/demo", tags=["Universal Demo Testing"])

DEMO_AUTHORIZED_ROLES = [
    UserRole.DEVELOPER,
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.SUB_ADMIN,
    UserRole.FACULTY,
]


@router.get("/models", response_model=ResponseEnvelope[DemoModelsResponse])
def get_available_demo_models(
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Returns the register of available face recognition models (Option 1, Option 3, Fine-Tuned).
    Allows easy switching between models in mobile and web visualizers.
    """
    data = DemoService.get_models_info()
    return ResponseEnvelope(data=data, correlation_id=correlation_id)


@router.post("/models/select", response_model=ResponseEnvelope[DemoModelsResponse])
def select_active_demo_model(
    payload: DemoSelectModelRequest,
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Switches the system-wide active demo model (Option 1 ArcFace 512-D, Option 3 SFace 128-D, etc.).
    """
    try:
        data = DemoService.set_active_model(payload.model_id)
        return ResponseEnvelope(data=data, correlation_id=correlation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.get("/enrolled-students", response_model=ResponseEnvelope[List[DemoEnrolledStudentSummary]])
def list_demo_students(
    department_code: Optional[str] = None,
    model_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Returns the enrolled students with registered face profiles, optionally filtered by department and model option.
    Sanitizes private biometric portraits and roll numbers for unauthenticated callers (SEC-02).
    """
    is_authorized = bool(current_user and current_user.role in DEMO_AUTHORIZED_ROLES)

    if current_user and current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
        if current_user.department:
            if department_code and department_code.strip().upper() not in (current_user.department.code.upper(), "ALL", ""):
                raise PermissionDeniedError(
                    f"Authorized solely for department {current_user.department.code}"
                )
            department_code = current_user.department.code

    students = DemoService.list_enrolled_demo_students(
        db, department_code=department_code, is_authorized=is_authorized, model_id=model_id
    )
    return ResponseEnvelope(data=students, correlation_id=correlation_id)


@router.post("/analyze", response_model=ResponseEnvelope[DemoAnalysisResponse])
async def analyze_demo_image(
    file: UploadFile = File(...),
    match_threshold: float = Form(0.363),
    margin_threshold: float = Form(0.10),
    blur_threshold: float = Form(25.0),
    department_code: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Processes a group or individual classroom photograph for ground-truth inspection:
    - Normalizes EXIF orientation so pixel coordinates match visual displays.
    - Executes model pipeline according to selected model (Option 1 ArcFace 512-D, Option 3 SFace 128-D).
    - Applies resolution-adaptive cosine thresholding for distant/crowd faces.
    - Searches against enrolled student identities (optionally scoped to a department).
    - Enforces bipartite mutual exclusivity to eliminate duplicate identity collisions.
    - Sanitizes reference photographs and full names for unauthenticated callers (SEC-02).
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zero-byte image payload rejected.",
        )

    try:
        is_authorized = bool(current_user and current_user.role in DEMO_AUTHORIZED_ROLES)

        if current_user and current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
            if current_user.department:
                if department_code and department_code.strip().upper() not in (current_user.department.code.upper(), "ALL", ""):
                    raise PermissionDeniedError(
                        f"Authorized solely for department {current_user.department.code}"
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
            model_id=model_id,
        )
        return ResponseEnvelope(data=result, correlation_id=correlation_id)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        ) from ve
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face analysis pipeline failure: {exc}",
        ) from exc
