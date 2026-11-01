"""
FRS V7.1 K² — Model Registry and Policy Version Models.
Prevents unapproved models or uncalibrated thresholds from operating in production.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ModelArtifact(Base):
    """
    Immutable model artifact record.
    SHA-256 hash confirms byte integrity; approval_status tracks legal and technical sign-off.
    """
    __tablename__ = "model_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(String(50), nullable=False)  # "DETECTION", "RECOGNITION", "PAD"
    format: Mapped[str] = mapped_column(String(20), default="ONNX", nullable=False)
    source_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    source_revision: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    code_license: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_license: Mapped[str] = mapped_column(String(100), nullable=False)
    data_provenance: Mapped[str] = mapped_column(String(255), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(30), default="PROVISIONAL", nullable=False)  # "APPROVED", "REJECTED"

    # Preprocessing contract bindings
    input_width: Mapped[int] = mapped_column(Integer, nullable=False)
    input_height: Mapped[int] = mapped_column(Integer, nullable=False)
    color_order: Mapped[str] = mapped_column(String(10), default="BGR", nullable=False)  # "BGR" or "RGB"
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=128, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PolicyVersion(Base):
    """
    Calibrated operational policy frozen to a session snapshot.
    Immutable once referenced by a finalized attendance session.
    """
    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "policy_kucet_v7_1_default"
    policy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    detector_model_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    recognizer_model_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Calibrated decision thresholds
    match_cosine_threshold: Mapped[float] = mapped_column(Float, default=0.45, nullable=False)
    margin_threshold: Mapped[float] = mapped_column(Float, default=0.10, nullable=False)
    min_face_size_pixels: Mapped[int] = mapped_column(Integer, default=32, nullable=False)

    # Conditional independent PAD gate
    pad_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pad_threshold: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("idx_policy_active", "is_active"),
    )
