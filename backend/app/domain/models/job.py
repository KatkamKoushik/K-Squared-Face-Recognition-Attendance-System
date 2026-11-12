"""
K² FRS — Bounded Vision Job Queue Model.
Supports atomic leasing, bounded retry backoff, and idempotent job execution.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.domain.enums import JobState, JobType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VisionJob(Base):
    """
    PostgreSQL-backed bounded queue job.
    Vision worker claims jobs using atomic UPDATE ... WHERE status='PENDING' ... RETURNING.
    """
    __tablename__ = "vision_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type: Mapped[JobType] = mapped_column(String(30), default=JobType.FRAME_DETECTION, nullable=False)
    frame_id: Mapped[str] = mapped_column(String(36), ForeignKey("frames.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), nullable=False)
    status: Mapped[JobState] = mapped_column(String(30), default=JobState.PENDING, nullable=False)

    worker_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_job_claim_scan", "status", "lease_expires_at", "attempt_count"),
    )
