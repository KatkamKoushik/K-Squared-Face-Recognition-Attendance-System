"""
FRS V7.1 K² — Academic Administration DTO Schemas.
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import AcademicTerm, EnrollmentStatus


class DepartmentCreate(BaseModel):
    code: str = Field(..., max_length=20, examples=["CSE", "ECE"])
    name: str = Field(..., max_length=100)


class DepartmentResponse(DepartmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool


class CohortCreate(BaseModel):
    department_id: str
    name: str = Field(..., max_length=50, examples=["CSE-2023-2027"])
    admission_year: int
    graduation_year: int


class CohortResponse(CohortCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool


class AcademicYearCreate(BaseModel):
    year_code: str = Field(..., max_length=20, examples=["2026-2027"])
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearResponse(AcademicYearCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


class TermCreate(BaseModel):
    academic_year_id: str
    term_type: AcademicTerm
    start_date: date
    end_date: date


class TermResponse(TermCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool


class SubjectCreate(BaseModel):
    code: str = Field(..., max_length=20, examples=["CS301"])
    name: str = Field(..., max_length=100)
    department_id: str
    credits: int = 3


class SubjectResponse(SubjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


class SubjectOfferingCreate(BaseModel):
    subject_id: str
    term_id: str
    primary_cohort_id: str
    section: str = "A"


class SubjectOfferingResponse(SubjectOfferingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    subjectName: Optional[str] = None
    cohort_name: Optional[str] = None
    cohort: Optional[str] = None
    enrolled_count: Optional[int] = None
    enrolledCount: Optional[int] = None


class AuthorizedClassGroupCreate(BaseModel):
    offering_id: str
    group_name: str
    cohort_ids: List[str] = Field(..., min_length=1)


class AuthorizedClassGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    offering_id: str
    group_name: str
    is_active: bool
    member_cohort_ids: List[str]


class FacultyAssignmentCreate(BaseModel):
    faculty_id: str
    offering_id: str
    class_group_id: Optional[str] = None
    start_date: date
    end_date: date


class FacultyAssignmentResponse(FacultyAssignmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool


class StudentCreate(BaseModel):
    roll_number: str = Field(..., max_length=50)
    institutional_email: Optional[str] = None
    full_name: str = Field(..., max_length=100)
    cohort_id: str


class StudentResponse(StudentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool


class EnrollmentCreate(BaseModel):
    student_id: str
    offering_id: str
    effective_start: date
    effective_end: Optional[date] = None


class EnrollmentResponse(EnrollmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: EnrollmentStatus
