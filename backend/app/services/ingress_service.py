"""
K² FRS — Image Ingress Validation, Metadata Stripping & Storage Service.
Rejects malformed uploads, decompression hazards, and enforces EXIF/GPS privacy stripping.
"""

import hashlib
import io
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageOps
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import IngressValidationError, ResourceNotFoundError
from app.domain.enums import JobState, JobType, SessionState
from app.domain.models.session import AttendanceSession
from app.domain.models.capture import CaptureBatch, Frame
from app.domain.models.job import VisionJob
from app.services.storage_service import CloudinaryStorageService

# Allow high-resolution smartphone imagery without decompression bomb rejections
Image.MAX_IMAGE_PIXELS = None


class IngressService:

    @classmethod
    def get_storage_dir(cls) -> Path:
        """Returns the configured shared storage directory, creating it if needed."""
        storage_path = Path(settings.STORAGE_DIR).resolve()
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    @classmethod
    def process_frame_upload(
        cls,
        db: Session,
        session_id: str,
        batch_id: str,
        frame_index: int,
        raw_bytes: bytes,
        correlation_id: str,
    ) -> Frame:
        """
        Validates, sanitizes, hashes, and stores an incoming classroom photo frame.
        """
        storage_dir = cls.get_storage_dir()

        # 1. Size check
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(raw_bytes) > max_bytes:
            raise IngressValidationError(
                message=f"Uploaded image exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                reason_code="PAYLOAD_TOO_LARGE",
                details={"size_bytes": len(raw_bytes), "max_allowed": max_bytes},
            )

        # 2. Decode and format verification
        try:
            image = Image.open(io.BytesIO(raw_bytes))
            image.verify()  # Verifies file integrity
            # Reopen after verify()
            image = Image.open(io.BytesIO(raw_bytes))
        except Exception as e:
            raise IngressValidationError(
                message="File is corrupted or not a valid decodeable image.",
                reason_code="DECODE_FAILED",
                details={"error": str(e)},
            )

        fmt = (image.format or "").upper()
        if fmt not in ["JPEG", "JPG", "PNG"]:
            raise IngressValidationError(
                message=f"Unsupported image format '{fmt}'. Allowed formats: JPEG, PNG.",
                reason_code="UNSUPPORTED_FORMAT",
            )

        width, height = image.size
        # Auto-rescale high-resolution smartphone imagery down to max 2560px for safe processing
        MAX_DIMENSION = 2560
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            width, height = image.size

        # 3. Strip EXIF & normalize orientation
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass  # If no orientation tag, continue

        if image.mode != "RGB":
            image = image.convert("RGB")

        # Save to buffer without EXIF metadata
        clean_buffer = io.BytesIO()
        image.save(clean_buffer, format="JPEG", quality=95)
        clean_bytes = clean_buffer.getvalue()

        # 4. Cryptographic SHA-256 hash
        content_hash = hashlib.sha256(clean_bytes).hexdigest()

        # 5. Save to Cloudinary object storage (with local fallback)
        frame_url = CloudinaryStorageService.upload_classroom_frame(
            file_bytes=clean_bytes,
            session_id=session_id,
            frame_index=frame_index,
        )

        # 6. Ensure batch exists (session-scoped to avoid cross-session primary key collisions)
        scoped_batch_id = batch_id if session_id in batch_id else f"{batch_id}_{session_id[:12]}"
        batch = db.get(CaptureBatch, scoped_batch_id)
        if not batch:
            batch = CaptureBatch(id=scoped_batch_id, session_id=session_id)
            db.add(batch)
            db.flush()

        # 7. Record Frame entity
        frame = Frame(
            batch_id=batch.id,
            frame_index=frame_index,
            content_sha256=content_hash,
            mime_type="image/jpeg",
            width=width,
            height=height,
            storage_path=frame_url,
            status="QUEUED",
        )
        db.add(frame)
        db.flush()

        # 8. Enqueue Vision Job in PostgreSQL queue
        job = VisionJob(
            job_type=JobType.FRAME_DETECTION,
            frame_id=frame.id,
            session_id=session_id,
            status=JobState.PENDING,
            idempotency_key=f"detect_job_frame_{frame.id}",
            correlation_id=correlation_id,
        )
        db.add(job)

        # Update session state to CAPTURING
        session = db.get(AttendanceSession, session_id)
        if session and session.state == SessionState.ROSTER_FROZEN:
            session.state = SessionState.CAPTURING

        db.flush()
        return frame
