"""
K² FRS — Real-Time Transactional Outbox Event Model.
Guarantees at-least-once delivery, cross-worker synchronization, and replayability across container restarts.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional
from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OutboxEvent(Base):
    """
    Append-only transactional outbox log.
    Ensures that business database mutations and event broadcasting are atomically committed.
    """
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_outbox_channel_created", "channel", "created_at"),
        Index("idx_outbox_pending_events", "is_published", "created_at"),
    )
