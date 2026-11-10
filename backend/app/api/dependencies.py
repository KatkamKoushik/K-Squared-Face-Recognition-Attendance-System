"""
FRS V7.1 K² — FastAPI Security & Route Dependencies.
Enforces scoped authentication, server-side RBAC, and request correlation tracing.
"""

import uuid
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.domain.enums import UserRole
from app.domain.models.academic import User, Faculty

security_scheme = HTTPBearer(auto_error=False)


def get_correlation_id(x_correlation_id: Optional[str] = Header(None)) -> str:
    """Extracts or generates an immutable correlation ID for request tracing."""
    return x_correlation_id or f"req-{uuid.uuid4().hex[:12]}"


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validates the Bearer token and returns the authenticated user."""
    if not auth:
        raise AuthenticationError("Authorization header missing or invalid", reason_code="TOKEN_MISSING")

    payload = decode_access_token(auth.credentials)
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token claims", reason_code="TOKEN_MALFORMED")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User is inactive or not found", reason_code="USER_NOT_ACTIVE")

    return user


def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional bearer token authentication; returns None if unauthenticated without rejecting."""
    if not auth:
        return None
    try:
        payload = decode_access_token(auth.credentials)
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            return None
        user = db.get(User, user_id)
        if user and user.is_active:
            return user
    except Exception:
        return None
    return None


def require_roles(allowed_roles: List[UserRole]):
    """Role-based authorization dependency guard."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError(
                message=f"Access denied: Operation requires one of {[r.value for r in allowed_roles]}.",
                reason_code="ROLE_NOT_AUTHORIZED",
            )
        return current_user
    return role_checker


def get_current_faculty(
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> Faculty:
    """Resolves the faculty profile linked to the authenticated user."""
    stmt = select(Faculty).where(Faculty.user_id == current_user.id)
    faculty = db.execute(stmt).scalar_one_or_none()
    if not faculty:
        raise PermissionDeniedError(
            message="Authenticated user does not have a linked faculty profile.",
            reason_code="FACULTY_PROFILE_NOT_FOUND",
        )
    return faculty
