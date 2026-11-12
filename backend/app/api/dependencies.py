"""
FRS V7.1 K² — FastAPI Security & Route Dependencies.
Enforces scoped authentication, server-side RBAC, and request correlation tracing.
"""

import uuid
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, Query, status
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
    token_param: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """Validates the Bearer token (internal JWT) and returns the authenticated user."""
    raw_token = auth.credentials if (auth and auth.credentials) else token_param
    if not raw_token or raw_token in ("null", "undefined"):
        raise AuthenticationError("Authorization header or token parameter missing or invalid", reason_code="TOKEN_MISSING")

    payload = verify_token(raw_token)

    # Session revocation hardening: raw Firebase ID tokens must be exchanged for an institutional session token
    if payload.get("firebase") is not None or payload.get("token_type") == "firebase_id_token":
        raise AuthenticationError(
            "Direct Firebase ID tokens are not permitted for institutional API requests. Please exchange your token via POST /api/v1/auth/firebase.",
            reason_code="SESSION_TOKEN_REQUIRED",
        )

    user_id = payload.get("user_id") or payload.get("sub")
    email = payload.get("email")

    user = None
    if user_id:
        user = db.get(User, user_id)
    if not user and email:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User is inactive or not found", reason_code="USER_NOT_ACTIVE")

    token_ver = payload.get("token_version")
    if token_ver is not None and token_ver != user.token_version:
        raise AuthenticationError("Session has been revoked or expired. Please log in again.", reason_code="TOKEN_REVOKED")

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
        firebase_uid = payload.get("firebase", {}).get("uid") if isinstance(payload.get("firebase"), dict) else None

        user = None
        if user_id:
            user = db.get(User, user_id)
        if not user and firebase_uid:
            user = db.execute(select(User).where(User.firebase_uid == firebase_uid)).scalar_one_or_none()
        if not user and email:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if user and user.is_active:
            token_ver = payload.get("token_version")
            if token_ver is not None and token_ver != user.token_version:
                return None
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
      If their department_id is missing/None, or target department_id is missing/None,
      they fail closed and cannot access any department.
    """
    if current_user.role in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN):
        return

    if not department_id:
        raise PermissionDeniedError(
            message="Operation requires an assigned department context.",
            reason_code="DEPARTMENT_ACCESS_RESTRICTED",
        )

    if current_user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
        if not current_user.department_id or current_user.department_id != department_id:
            raise PermissionDeniedError(
                message=f"Access denied: User is isolated to department '{current_user.department_id}' and cannot access department '{department_id}'.",
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
