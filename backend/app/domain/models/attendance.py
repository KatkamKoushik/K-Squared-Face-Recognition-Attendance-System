"""
FRS V7.1 K² — Authoritative Attendance Ledger Model.
Enforces the ACID attendance denominator: per student per conducted instructional unit.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.domain.enums import AttendanceStatus, AppealStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AttendanceRecord(Base):
    """
    The authoritative, human-confirmed finalized attendance record.
    Uniquely indexed on (session_id, unit_id, student_id).
    """
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_units.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(String(30), default=AttendanceStatus.PRESENT_CONFIRMED, nullable=False)
    finalized_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(50), default="FACULTY_COMMIT", nullable=False)

    # Lineage link to evidence if match was camera-derived
    source_evidence_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("face_evidences.id"), nullable=True)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("Student")
    unit = relationship("AttendanceUnit")
    finalized_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("session_id", "unit_id", "student_id", name="uq_attendance_ledger_unit_student"),
        Index("idx_attendance_student_query", "student_id", "status"),
        Index("idx_attendance_session_unit", "session_id", "unit_id"),
    )


class AttendanceAppeal(Base):
    """
    Formal student attendance appeal or dispute record.
    Allows a student to contest an ABSENT record with reasons and supporting documentation.
    """
    __tablename__ = "attendance_appeals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_units.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[AppealStatus] = mapped_column(String(30), default=AppealStatus.PENDING, nullable=False, index=True)
    review_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reviewed_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    student = relationship("Student")
    session = relationship("AttendanceSession")
    unit = relationship("AttendanceUnit")
    reviewed_by = relationship("User")

    __table_args__ = (
        Index("idx_appeal_student_status", "student_id", "status"),
        Index("idx_appeal_session_unit", "session_id", "unit_id"),
    )

