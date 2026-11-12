"""
FRS V7.1 K² — Academic Core Domain Models.
Implements Departments, Cohorts, Terms, Subjects, Offerings, Groups, and Assignments.
"""

from datetime import date, datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.domain.enums import AcademicTerm, UserRole


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.FACULTY, nullable=False)
    department_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    department: Mapped[Optional["Department"]] = relationship("Department")
    faculty_profile: Mapped[Optional["Faculty"]] = relationship("Faculty", back_populates="user", uselist=False)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    cohorts: Mapped[List["Cohort"]] = relationship("Cohort", back_populates="department")
    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="department")


class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "CSE-2023-2027"
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    department: Mapped["Department"] = relationship("Department", back_populates="cohorts")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="cohort")

    __table_args__ = (
        UniqueConstraint("department_id", "name", name="uq_cohort_dept_name"),
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    year_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. "2026-2027"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id"), nullable=False)
    term_type: Mapped[AcademicTerm] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    offerings: Mapped[List["SubjectOffering"]] = relationship("SubjectOffering", back_populates="term")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    department: Mapped["Department"] = relationship("Department", back_populates="subjects")
    offerings: Mapped[List["SubjectOffering"]] = relationship("SubjectOffering", back_populates="subject")


class SubjectOffering(Base):
    __tablename__ = "subject_offerings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id"), nullable=False)
    term_id: Mapped[str] = mapped_column(String(36), ForeignKey("terms.id"), nullable=False)
    primary_cohort_id: Mapped[str] = mapped_column(String(36), ForeignKey("cohorts.id"), nullable=False)
    section: Mapped[str] = mapped_column(String(10), default="A", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="offerings")
    term: Mapped["Term"] = relationship("Term", back_populates="offerings")
    faculty_assignments: Mapped[List["FacultyAssignment"]] = relationship("FacultyAssignment", back_populates="offering")
    approved_groups: Mapped[List["AuthorizedClassGroup"]] = relationship("AuthorizedClassGroup", back_populates="offering")

    __table_args__ = (
        UniqueConstraint("subject_id", "term_id", "primary_cohort_id", "section", name="uq_offering_identity"),
    )


class AuthorizedClassGroup(Base):
    """Explicitly approved joint-class group combining cohorts for an offering."""
    __tablename__ = "authorized_class_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("subject_offerings.id"), nullable=False)
    group_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    offering: Mapped["SubjectOffering"] = relationship("SubjectOffering", back_populates="approved_groups")
    member_cohorts: Mapped[List["ClassGroupMemberCohort"]] = relationship("ClassGroupMemberCohort", back_populates="group")


class ClassGroupMemberCohort(Base):
    __tablename__ = "class_group_member_cohorts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("authorized_class_groups.id"), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(36), ForeignKey("cohorts.id"), nullable=False)

    group: Mapped["AuthorizedClassGroup"] = relationship("AuthorizedClassGroup", back_populates="member_cohorts")
    cohort: Mapped["Cohort"] = relationship("Cohort")

    __table_args__ = (
        UniqueConstraint("group_id", "cohort_id", name="uq_group_cohort_membership"),
    )


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="faculty_profile")
    assignments: Mapped[List["FacultyAssignment"]] = relationship("FacultyAssignment", back_populates="faculty")


class FacultyAssignment(Base):
    """Server-side check: faculty must have effective assignment to teach/commit attendance."""
    __tablename__ = "faculty_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_id: Mapped[str] = mapped_column(String(36), ForeignKey("faculty.id"), nullable=False)
    offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("subject_offerings.id"), nullable=False)
    class_group_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("authorized_class_groups.id"), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="assignments")
    offering: Mapped["SubjectOffering"] = relationship("SubjectOffering", back_populates="faculty_assignments")

    __table_args__ = (
        Index("idx_faculty_assignment_effective", "faculty_id", "offering_id", "is_active"),
    )
