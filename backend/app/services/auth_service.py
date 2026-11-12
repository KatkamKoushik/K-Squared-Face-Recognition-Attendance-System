"""
FRS V7.1 K² — Authentication & User Management Service.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import AuthenticationError, PermissionDeniedError, ResourceNotFoundError, BusinessRuleViolationError
from app.core.security import verify_password, create_access_token, hash_password, verify_firebase_id_token
from app.domain.enums import UserRole
from app.domain.models.academic import User, Faculty
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, FirebaseLoginRequest


class AuthService:

    @staticmethod
    def _issue_user_token(db: Session, user: User) -> TokenResponse:
        """Builds scoped claims and issues a fresh signed institutional JWT."""
        if not user.is_active:
            raise AuthenticationError("User account is inactive", reason_code="USER_INACTIVE")

        faculty_id = None
        if user.role in (UserRole.FACULTY, UserRole.SUB_ADMIN):
            fac_result = db.execute(select(Faculty).where(Faculty.user_id == user.id))
            fac = fac_result.scalar_one_or_none()
            if fac:
                faculty_id = fac.id

        claims = {
            "user_id": user.id,
            "token_version": user.token_version,
        }
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
    def authenticate_firebase_token(db: Session, creds: FirebaseLoginRequest) -> TokenResponse:
        decoded = verify_firebase_id_token(creds.id_token)
        firebase_uid = decoded.get("uid") or decoded.get("user_id")
        email = decoded.get("email")
        email_verified = decoded.get("email_verified", False)
        if isinstance(decoded.get("firebase"), dict):
            email_verified = decoded["firebase"].get("email_verified", email_verified)

        user = None
        if firebase_uid:
            user = db.execute(select(User).where(User.firebase_uid == firebase_uid)).scalar_one_or_none()

        if not user:
            if not email:
                raise AuthenticationError("Firebase token contains no verified email", reason_code="FIREBASE_EMAIL_MISSING")

            if not email_verified:
                raise AuthenticationError(
                    "Firebase email address has not been verified. Email verification is strictly required before institutional account linking.",
                    reason_code="EMAIL_NOT_VERIFIED",
                )

            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if user and firebase_uid and not user.firebase_uid:
                user.firebase_uid = firebase_uid
                from app.domain.models.audit import AuditEvent
                from app.domain.enums import AuditAction
                audit = AuditEvent(
                    session_id=None,
                    actor_id=user.id,
                    action=AuditAction.FIREBASE_IDENTITY_LINKED,
                    reason=f"Firebase UID '{firebase_uid}' linked to user '{user.email}' after cryptographic email verification.",
                    before_state={"firebase_uid": None},
                    after_state={"firebase_uid": firebase_uid, "role": user.role.value if hasattr(user.role, "value") else str(user.role)},
                    correlation_id=f"fb-link-{user.id[:8]}",
                )
                db.add(audit)
                db.commit()

        if not user:
            raise AuthenticationError(
                f"Firebase identity '{email or firebase_uid}' is not registered in institutional directory.",
                reason_code="USER_NOT_REGISTERED",
            )

        return AuthService._issue_user_token(db, user)

    @staticmethod
    def authenticate_user(db: Session, creds: LoginRequest) -> TokenResponse:
        result = db.execute(select(User).where(User.email == creds.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(creds.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password", reason_code="INVALID_CREDENTIALS")

        return AuthService._issue_user_token(db, user)

    @staticmethod
    def refresh_user_token(db: Session, user: User) -> TokenResponse:
        return AuthService._issue_user_token(db, user)

    @staticmethod
    def logout_user(db: Session, user: User) -> None:
        user.token_version += 1
        db.commit()

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect", reason_code="INVALID_CREDENTIALS")
        if len(new_password) < 8:
            raise BusinessRuleViolationError("New password must be at least 8 characters long.", reason_code="WEAK_PASSWORD")
        user.hashed_password = hash_password(new_password)
        user.token_version += 1
        db.commit()

    @staticmethod
    def update_user_status(
        db: Session,
        target_user_id: str,
        is_active: bool,
        actor: User,
        reason: Optional[str] = None,
    ) -> User:
        target = db.get(User, target_user_id)
        if not target:
            raise ResourceNotFoundError("User", target_user_id)

        if actor.role == UserRole.ADMIN:
            if not actor.department_id or target.department_id != actor.department_id:
                raise PermissionDeniedError(
                    message="Department administrator can only manage user accounts within their assigned department.",
                    reason_code="DEPARTMENT_ACCESS_RESTRICTED",
                )
            if target.role in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN):
                raise PermissionDeniedError(
                    message="Department administrator cannot modify institutional or developer accounts.",
                    reason_code="ROLE_NOT_AUTHORIZED",
                )

        target.is_active = is_active
        if not is_active:
            target.token_version += 1
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
            department_id=data.department_id,
        )
        db.add(user)
        db.flush()
        return user
