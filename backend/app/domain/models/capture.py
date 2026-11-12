"""
K² FRS — Capture Batch, Image Frame, and Face Evidence Domain Models.
Enforces content hashes, size boundaries, and typed per-face evidence traces.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy import (
    String,
    Float,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.domain.enums import EvidenceState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CaptureBatch(Base):
    __tablename__ = "capture_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("attendance_sessions.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session = relationship("AttendanceSession", back_populates="batches")
    frames: Mapped[List["Frame"]] = relationship("Frame", back_populates="batch", cascade="all, delete-orphan")


class Frame(Base):
    """
    Classroom capture frame with cryptographic SHA-256 hash.
    Image files are stored in access-controlled temporary storage.
    """
    __tablename__ = "frames"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("capture_batches.id"), nullable=False)
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), default="image/jpeg", nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="RECEIVED", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    batch: Mapped["CaptureBatch"] = relationship("CaptureBatch", back_populates="frames")
    faces: Mapped[List["FaceEvidence"]] = relationship("FaceEvidence", back_populates="frame", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("batch_id", "frame_index", name="uq_batch_frame_index"),
        Index("idx_frame_sha256", "content_sha256"),
    )


class FaceEvidence(Base):
    """
    Per-face typed evidence record discovered in a classroom frame.
    Separates detection confidence, quality assessment, and open-set candidate match.
    """
    __tablename__ = "face_evidences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    frame_id: Mapped[str] = mapped_column(String(36), ForeignKey("frames.id"), nullable=False)
    # Normalized bounding box coordinates [0.0 - 1.0]
    box_x1: Mapped[float] = mapped_column(Float, nullable=False)
    box_y1: Mapped[float] = mapped_column(Float, nullable=False)
    box_x2: Mapped[float] = mapped_column(Float, nullable=False)
    box_y2: Mapped[float] = mapped_column(Float, nullable=False)
    detection_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Per-face quality
    quality_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    quality_reason: Mapped[str] = mapped_column(String(50), default="NORMAL", nullable=False)

    # Match Candidate (Evidence Producer only — NOT final attendance)
    candidate_student_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("students.id"), nullable=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Pipeline evidence classification
    evidence_state: Mapped[EvidenceState] = mapped_column(String(30), default=EvidenceState.PROCESSING, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(50), default="PENDING_ANALYSIS", nullable=False)

    # Model and artifact audit trace
    model_artifact_hash: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    frame: Mapped["Frame"] = relationship("Frame", back_populates="faces")
    candidate_student = relationship("Student")

    __table_args__ = (
        Index("idx_evidence_state", "evidence_state"),
        Index("idx_evidence_student", "candidate_student_id"),
    )
