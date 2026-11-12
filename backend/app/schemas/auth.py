"""
FRS V7.1 K² — Authentication & User Contracts.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from app.domain.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
    is_active: bool


class FacultyProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    employee_id: str
    full_name: str
    department_id: str
