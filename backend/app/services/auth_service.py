"""
FRS V7.1 K² — Authentication & User Management Service.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import AuthenticationError
from app.core.security import verify_password, create_access_token, hash_password
from app.domain.enums import UserRole
from app.domain.models.academic import User, Faculty
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate


class AuthService:

    @staticmethod
    def authenticate_user(db: Session, creds: LoginRequest) -> TokenResponse:
        result = db.execute(select(User).where(User.email == creds.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(creds.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password", reason_code="INVALID_CREDENTIALS")

        if not user.is_active:
            raise AuthenticationError("User account is inactive", reason_code="USER_INACTIVE")

        # Resolve faculty ID if faculty
        faculty_id = None
        if user.role == UserRole.FACULTY:
            fac_result = db.execute(select(Faculty).where(Faculty.user_id == user.id))
            fac = fac_result.scalar_one_or_none()
            if fac:
                faculty_id = fac.id

        claims = {"user_id": user.id}
        if user.department_id:
            claims["department_id"] = user.department_id
        if faculty_id:
            claims["faculty_id"] = faculty_id

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        role_enum = user.role if isinstance(user.role, UserRole) else UserRole(role_str)
        token = create_access_token(
            subject=user.email,
            role=role_str,
            additional_claims=claims,
        )
        return TokenResponse(
            access_token=token,
            expires_in_minutes=60,
            user_id=user.id,
            role=role_enum,
            email=user.email,
            department_id=user.department_id,
        )

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        db.add(user)
        db.flush()
        return user
