"""
K² FRS — Attendance Session, Conducted Units, and Immutable Roster Snapshot Models.
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
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.domain.enums import SessionState, UnitStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AttendanceSession(Base):
    """
    Teacher-operated attendance session for an assigned offering or joint-class group.
    Maintains immutable pointer to the frozen roster snapshot and policy version.
    """
    __tablename__ = "attendance_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offering_id: Mapped[str] = mapped_column(String(36), ForeignKey("subject_offerings.id"), nullable=False)
    class_group_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("authorized_class_groups.id"), nullable=True)
    faculty_id: Mapped[str] = mapped_column(String(36), ForeignKey("faculty.id"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    state: Mapped[SessionState] = mapped_column(String(20), default=SessionState.DRAFT, nullable=False)
    policy_version_id: Mapped[str] = mapped_column(String(50), default="policy_kucet_k2_default", nullable=False)
    planned_units: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 to 4 units
    model_version: Mapped[Optional[str]] = mapped_column(String(100), default="yunet_2023mar_sface_2021dec", nullable=True)
    calibration_threshold: Mapped[Optional[float]] = mapped_column(Float, default=0.363, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    units: Mapped[List["AttendanceUnit"]] = relationship("AttendanceUnit", back_populates="session", cascade="all, delete-orphan")
    snapshot: Mapped[Optional["RosterSnapshot"]] = relationship("RosterSnapshot", back_populates="session", uselist=False)
    batches: Mapped[List["CaptureBatch"]] = relationship("CaptureBatch", back_populates="session")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="session")

    __table_args__ = (
        Index("idx_session_faculty_date", "faculty_id", "session_date", "state"),
    )


class AttendanceUnit(Base):
    """
    Individual instructional unit (1 to 4) conducted within a session.
    Faculty must explicitly confirm which units were conducted before final commit.
    """
    __tablename__ = "attendance_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), nullable=False)
    unit_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, or 4
    is_conducted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[UnitStatus] = mapped_column(String(30), default=UnitStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped["AttendanceSession"] = relationship("AttendanceSession", back_populates="units")

    __table_args__ = (
        UniqueConstraint("session_id", "unit_index", name="uq_session_unit_index"),
    )


class RosterSnapshot(Base):
    """
    Frozen snapshot of eligible enrolled students at the time the session was initialized.
    Live mutations to enrollments cannot retroactively alter an existing session's roster.
    """
    __tablename__ = "roster_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), unique=True, nullable=False)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_eligible_students: Mapped[int] = mapped_column(Integer, nullable=False)
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped["AttendanceSession"] = relationship("AttendanceSession", back_populates="snapshot")
    items: Mapped[List["SnapshotStudentItem"]] = relationship("SnapshotStudentItem", back_populates="snapshot", cascade="all, delete-orphan")


class SnapshotStudentItem(Base):
    __tablename__ = "snapshot_student_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("roster_snapshots.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(36), nullable=False)

    snapshot: Mapped["RosterSnapshot"] = relationship("RosterSnapshot", back_populates="items")

    __table_args__ = (
        UniqueConstraint("snapshot_id", "student_id", name="uq_snapshot_student"),
    )
