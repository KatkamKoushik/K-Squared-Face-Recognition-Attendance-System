"""
K² FRS — Commit Receipts and Append-Only Audit Trail Models.
Provides durable transaction receipts and verifiable accountability.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.domain.enums import AuditAction


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommitReceipt(Base):
    """
    Durable proof returned upon attendance commit.
    Replaying the same idempotency key returns this identical receipt.
    """
    __tablename__ = "commit_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    committed_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    total_conducted_units: Mapped[int] = mapped_column(Integer, nullable=False)
    total_present_records: Mapped[int] = mapped_column(Integer, nullable=False)
    total_absent_records: Mapped[int] = mapped_column(Integer, nullable=False)
    receipt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(100), default="yunet_2023mar_sface_2021dec", nullable=True)
    calibration_threshold: Mapped[Optional[float]] = mapped_column(Float, default=0.363, nullable=True)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    """
    Append-only application audit event log.
    Records every critical lifecycle change, before/after values, and actor correlation.
    """
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[AuditAction] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_audit_session_action", "session_id", "action"),
        Index("idx_audit_actor_time", "actor_id", "timestamp"),
    )
