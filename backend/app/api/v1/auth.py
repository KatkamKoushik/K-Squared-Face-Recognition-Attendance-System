"""
FRS V7.1 K² — Authentication Endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_correlation_id, require_roles
from app.core.database import get_db
from app.domain.enums import UserRole
from app.domain.models.academic import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    FirebaseLoginRequest,
    UserStatusUpdateRequest,
    ChangePasswordRequest,
)
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


@router.post("/firebase", response_model=ResponseEnvelope[TokenResponse])
def firebase_login(
    creds: FirebaseLoginRequest,
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """Exchanges a verified Firebase ID token for a scoped institutional JWT token."""
    token = AuthService.authenticate_firebase_token(db, creds)
    return ResponseEnvelope(data=token, correlation_id=correlation_id)


@router.get("/me", response_model=ResponseEnvelope[UserResponse])
def get_me(
    current_user: User = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id),
):
    """Returns currently authenticated user profile."""
    return ResponseEnvelope(data=UserResponse.model_validate(current_user), correlation_id=correlation_id)


@router.post("/refresh", response_model=ResponseEnvelope[TokenResponse])
def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """Issues a refreshed JWT token for the currently authenticated session."""
    refreshed = AuthService.refresh_user_token(db, current_user)
    return ResponseEnvelope(data=refreshed, correlation_id=correlation_id)


@router.post("/logout", response_model=ResponseEnvelope[dict])
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """Revokes the current user's session by rotating their token version."""
    AuthService.logout_user(db, current_user)
    return ResponseEnvelope(data={"message": "Logged out successfully. Session revoked."}, correlation_id=correlation_id)


@router.post("/change-password", response_model=ResponseEnvelope[dict])
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """Changes password for the current user and revokes all older active sessions."""
    AuthService.change_password(db, current_user, req.current_password, req.new_password)
    return ResponseEnvelope(data={"message": "Password updated successfully. Prior sessions revoked."}, correlation_id=correlation_id)


@router.patch("/users/{user_id}/status", response_model=ResponseEnvelope[UserResponse])
def update_user_status(
    user_id: str,
    req: UserStatusUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """Super Admin or Department Admin activates, suspends, or deactivates a user account."""
    updated = AuthService.update_user_status(
        db=db,
        target_user_id=user_id,
        is_active=req.is_active,
        actor=current_user,
        reason=req.reason,
    )
    return ResponseEnvelope(data=UserResponse.model_validate(updated), correlation_id=correlation_id)
