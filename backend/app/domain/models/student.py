"""
FRS V7.1 K² — Student Identity, Enrollment, and Template Profile Models.
Enforces institutional student identity and effective-dated enrollment truth.
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
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.domain.enums import EnrollmentStatus, EnrollmentSubmissionStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    institutional_email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(36), ForeignKey("cohorts.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    cohort = relationship("Cohort", back_populates="students")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="student")
    profiles: Mapped[List["EnrollmentProfile"]] = relationship("EnrollmentProfile", back_populates="student")


class Enrollment(Base):
    """Effective-dated enrollment truth linking student to academic subject offering."""
    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("subject_offerings.id"), nullable=False)
    status: Mapped[EnrollmentStatus] = mapped_column(String(20), default=EnrollmentStatus.ACTIVE, nullable=False)
    effective_start: Mapped[date] = mapped_column(Date, nullable=False)
    effective_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "offering_id", name="uq_student_offering_enrollment"),
        Index("idx_enrollment_effective", "offering_id", "status"),
    )


class EnrollmentProfile(Base):
    """
    Registered face embedding template for exact roster-scoped 1:N search.
    Stored with model provenance hash and embedding namespace.
    """
    __tablename__ = "enrollment_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    model_artifact_id: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., SHA256 of recognizer
    embedding_namespace: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "sface_128d_v1"
    embedding_dimension: Mapped[int] = mapped_column(default=128, nullable=False)
    # Normalized L2 embedding coordinates stored safely as JSON list of floats
    vector_data: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    profile_version: Mapped[int] = mapped_column(default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student: Mapped["Student"] = relationship("Student", back_populates="profiles")

    __table_args__ = (
        Index("idx_profile_search", "student_id", "embedding_namespace", "is_active"),
    )


class EnrollmentSubmission(Base):
    """
    Staged student biometric enrollment submission for administrative verification.
    Follows strict lifecycle: PENDING_REVIEW -> APPROVED / REJECTED / RECAPTURE_REQUIRED / WITHDRAWN.
    Stored photographs reside in private access-controlled storage; never served publicly.
    """
    __tablename__ = "enrollment_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    roll_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    institutional_email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(50), nullable=False)
    cohort_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("cohorts.id"), nullable=True)

    photo_storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    photo_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    photo_mime: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[EnrollmentSubmissionStatus] = mapped_column(
        String(30), default=EnrollmentSubmissionStatus.PENDING_REVIEW, nullable=False, index=True
    )
    consent_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    reviewed_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    cohort = relationship("Cohort")
    reviewed_by = relationship("User")

    __table_args__ = (
        Index("idx_submission_status_created", "status", "created_at"),
        Index("idx_submission_roll", "roll_number"),
    )
