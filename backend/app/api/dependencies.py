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
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token, verify_token
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
    """Validates the Bearer token (internal JWT or Firebase) and returns the authenticated user."""
    if not auth or not auth.credentials or auth.credentials in ("null", "undefined"):
        raise AuthenticationError("Authorization header missing or invalid", reason_code="TOKEN_MISSING")

    payload = verify_token(auth.credentials)
    user_id = payload.get("user_id") or payload.get("sub")
    email = payload.get("email")

    user = None
    if user_id:
        user = db.get(User, user_id)
    if not user and email:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

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
        payload = verify_token(auth.credentials)
        user_id = payload.get("user_id") or payload.get("sub")
        email = payload.get("email")

        user = None
        if user_id:
            user = db.get(User, user_id)
        if not user and email:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if user and user.is_active:
            return user
    except Exception:
        return None
    return None


def require_roles(allowed_roles: List[UserRole]):
    """Role-based authorization dependency guard with 5-tier hierarchical inheritance."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role
        is_authorized = user_role in allowed_roles

        # DEVELOPER possesses unrestricted system-wide authority across all tiers
        if user_role == UserRole.DEVELOPER:
            is_authorized = True
        # SUPER_ADMIN possesses campus-wide institutional authority and satisfies ADMIN, SUB_ADMIN, FACULTY requirements
        elif user_role == UserRole.SUPER_ADMIN:
            if any(r in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY) for r in allowed_roles):
                is_authorized = True
        # SUB_ADMIN and FACULTY are equivalent faculty tiers
        elif user_role == UserRole.SUB_ADMIN and (UserRole.FACULTY in allowed_roles or UserRole.SUB_ADMIN in allowed_roles):
            is_authorized = True
        elif user_role == UserRole.FACULTY and (UserRole.SUB_ADMIN in allowed_roles or UserRole.FACULTY in allowed_roles):
            is_authorized = True

        if not is_authorized:
            raise PermissionDeniedError(
                message=f"Access denied: Operation requires one of {[r.value for r in allowed_roles]}.",
                reason_code="ROLE_NOT_AUTHORIZED",
            )
        return current_user
    return role_checker


def check_department_access(current_user: User, department_id: Optional[str]) -> None:
    """
    Enforces strict department scoping:
    - DEVELOPER and SUPER_ADMIN have campus-wide access across all departments.
    - ADMIN, SUB_ADMIN, and FACULTY are strictly restricted to their assigned department.
      If their department_id is missing/None, they fail closed and cannot access any department.
    """
    if not department_id:
        return
    if current_user.role in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN):
        return
    if current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
        if not current_user.department_id or current_user.department_id != department_id:
            raise PermissionDeniedError(
                message="Access denied: Department administrator cannot access or modify records without an assigned department or across another department.",
                reason_code="DEPARTMENT_ACCESS_RESTRICTED",
            )


def get_current_faculty(
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.SUB_ADMIN, UserRole.ADMIN])),
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
