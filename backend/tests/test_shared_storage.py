"""
K² FRS -- Shared Storage Architecture & Worker Access Tests.
Verifies that ingress API persists frames to configured STORAGE_DIR and
that vision worker resolves and processes frames from that shared path.
"""

import io
import os
import pytest
from pathlib import Path
from PIL import Image
from sqlalchemy.orm import Session
from app.core.config import settings
from app.domain.enums import SessionState
from app.domain.models.session import AttendanceSession, RosterSnapshot
from app.domain.models.capture import Frame
from app.domain.models.job import VisionJob
from app.services.ingress_service import IngressService
from app.worker.worker import VisionWorker


def test_ingress_saves_frame_to_configured_storage_dir(db_session: Session, seed_data):
    """
    P0.6: Frame ingress must persist bytes into settings.STORAGE_DIR,
    record absolute storage_path, and strip metadata.
    """
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.ROSTER_FROZEN,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    # Generate a valid clean JPEG
    img = Image.new("RGB", (320, 240), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    frame = IngressService.process_frame_upload(
        db=db_session,
        session_id=session.id,
        batch_id="batch_shared_01",
        frame_index=0,
        raw_bytes=raw_bytes,
        correlation_id="corr_storage_01",
    )

    # Verify frame is saved under configured Cloudinary or local STORAGE_DIR
    if frame.storage_path.startswith("http://") or frame.storage_path.startswith("https://"):
        assert "res.cloudinary.com" in frame.storage_path or "cloudinary" in frame.storage_path
        from app.services.storage_service import CloudinaryStorageService
        retrieved_bytes = CloudinaryStorageService.load_image_bytes(frame.storage_path)
        assert len(retrieved_bytes) > 0
    else:
        expected_storage_dir = Path(settings.STORAGE_DIR).resolve()
        actual_frame_path = Path(frame.storage_path).resolve()
        assert expected_storage_dir in actual_frame_path.parents or actual_frame_path.parent == expected_storage_dir
        assert os.path.exists(actual_frame_path)
        assert os.path.getsize(actual_frame_path) > 0


def test_worker_fails_gracefully_when_frame_storage_file_missing(db_session: Session, seed_data):
    """
    P0.6: Vision worker must detect missing shared volume files and raise
    descriptive FileNotFoundError for retryable queue handling.
    """
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.CAPTURING,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=0)
    db_session.add(snapshot)
    db_session.flush()

    missing_path = str(Path(settings.STORAGE_DIR).resolve() / "non_existent_frame_12345.jpg")
    frame = Frame(
        batch_id="batch_missing_01",
        frame_index=0,
        content_sha256="0" * 64,
        mime_type="image/jpeg",
        width=320,
        height=240,
        storage_path=missing_path,
        status="QUEUED",
    )
    db_session.add(frame)
    db_session.flush()

    job = VisionJob(
        job_type="FRAME_DETECTION",
        frame_id=frame.id,
        session_id=session.id,
        status="PENDING",
        idempotency_key="job_missing_test",
        correlation_id="corr_missing",
    )
    db_session.add(job)
    db_session.flush()

    worker = VisionWorker(worker_id="test_worker")
    with pytest.raises(FileNotFoundError, match="Frame image not found at storage path"):
        worker.execute_job(db_session, job)
