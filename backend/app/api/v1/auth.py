"""
FRS V7.1 K² — Authentication Endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_correlation_id
from app.core.database import get_db
from app.domain.models.academic import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.common import ResponseEnvelope
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
def login(
    creds: LoginRequest,
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """Issues scoped JWT token for faculty or administrator."""
    token = AuthService.authenticate_user(db, creds)
    return ResponseEnvelope(data=token, correlation_id=correlation_id)


@router.get("/me", response_model=ResponseEnvelope[UserResponse])
def get_me(
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Returns currently authenticated user profile."""
    return ResponseEnvelope(data=UserResponse.model_validate(current_user), correlation_id=correlation_id)
