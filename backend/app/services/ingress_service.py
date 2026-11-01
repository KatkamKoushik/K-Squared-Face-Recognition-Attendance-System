"""
FRS V7.1 K² — Image Ingress Validation, Metadata Stripping & Storage Service.
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

# Restrict PIL max pixels to prevent memory exhaustion / decompression bomb attacks
Image.MAX_IMAGE_PIXELS = 4096 * 4096


class IngressService:

    STORAGE_DIR = Path(tempfile.gettempdir()) / "frs_temp_storage"

    @classmethod
    def ensure_storage_dir(cls):
        cls.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

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
        cls.ensure_storage_dir()

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
        if width > settings.MAX_IMAGE_WIDTH or height > settings.MAX_IMAGE_HEIGHT:
            raise IngressValidationError(
                message=f"Image dimensions {width}x{height} exceed limits ({settings.MAX_IMAGE_WIDTH}x{settings.MAX_IMAGE_HEIGHT}).",
                reason_code="DIMENSIONS_EXCEEDED",
            )

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

        # 5. Save to private temporary storage
        filename = f"{content_hash}_{frame_index}.jpg"
        file_path = cls.STORAGE_DIR / filename
        with open(file_path, "wb") as f:
            f.write(clean_bytes)

        # 6. Ensure batch exists
        batch_stmt = select(CaptureBatch).where(
            and_(CaptureBatch.id == batch_id, CaptureBatch.session_id == session_id)
        )
        batch = db.execute(batch_stmt).scalar_one_or_none()
        if not batch:
            batch = CaptureBatch(id=batch_id, session_id=session_id)
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
            storage_path=str(file_path),
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
