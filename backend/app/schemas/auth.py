"""
K² FRS — Authentication & User Contracts.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from app.domain.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class FirebaseLoginRequest(BaseModel):
    id_token: str
    remember: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: str
    role: UserRole
    email: str
    department_id: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.FACULTY
    department_id: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: UserRole
    department_id: Optional[str] = None
    firebase_uid: Optional[str] = None
    is_active: bool


class UserStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class FacultyProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    employee_id: str
    full_name: str
    department_id: str
