"""
FRS V7.1 K² — Deterministic Vision Orchestration State Machine & Worker Processor.
Processes queued frames, enforces per-face evidence routing, and prepares candidate proposals.
"""

import logging
import os
from typing import Dict, List
import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger("app.worker")
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session
from app.domain.enums import EvidenceState, SessionState
from app.domain.models.session import AttendanceSession, RosterSnapshot
from app.domain.models.capture import Frame, FaceEvidence
from app.domain.models.student import EnrollmentProfile
from app.domain.models.job import VisionJob
from app.services.queue_service import QueueService
from app.worker.preprocessor import Preprocessor
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from app.worker.adapters.pad_adapter import PadAdapter


class VisionWorker:

    def __init__(self, worker_id: str = "vision_worker_01"):
        self.worker_id = worker_id
        self.detector = DetectorAdapter()
        self.recognizer = RecognizerAdapter()
        self.pad = PadAdapter()

    def process_batch(self, db: Session, limit: int = 5) -> int:
        """Claims and executes a bounded batch of queued vision jobs."""
        jobs = QueueService.claim_jobs(db, self.worker_id, limit=limit)
        processed_count = 0

        for job in jobs:
            try:
                self.process_job(db, job)
                processed_count += 1
            except Exception as e:
                QueueService.record_job_failure(
                    db, job.id, error_message=str(e), retryable=True
                )

        return processed_count

    def process_job(self, db: Session, job: VisionJob):
        """Processes a single vision job through the state machine pipeline."""
        self.execute_job(db, job)
        QueueService.complete_job(db, job.id, self.worker_id, success=True)

    def execute_job(self, db: Session, job: VisionJob):
        """Executes full pipeline for one classroom frame."""
        frame = db.get(Frame, job.frame_id)
        if not frame:
            raise ValueError(f"Frame {job.frame_id} not found")

        # 1. Fetch session and enrolled templates
        session_stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.snapshot).selectinload(RosterSnapshot.items)
            )
            .where(AttendanceSession.id == job.session_id)
        )
        session = db.execute(session_stmt).scalar_one_or_none()
        if not session or not session.snapshot:
            raise ValueError(f"Session {job.session_id} lacks frozen roster snapshot")

        eligible_student_ids = [item.student_id for item in session.snapshot.items]

        # Fetch enrolled profile vectors for eligible students
        profiles_stmt = select(EnrollmentProfile).where(
            EnrollmentProfile.student_id.in_(eligible_student_ids),
            EnrollmentProfile.is_active == True,
        )
        profiles = list(db.execute(profiles_stmt).scalars().all())
        roster_gallery: Dict[str, List[float]] = {p.student_id: p.vector_data for p in profiles}

        # 2. Open frame image from shared storage
        if not os.path.exists(frame.storage_path):
            raise FileNotFoundError(
                f"Frame image not found at storage path: {frame.storage_path}. "
                "Ensure shared frame_storage volume is mounted for both API and vision-worker."
            )
        image = Image.open(frame.storage_path)

        # 3. Detect faces
        detections = self.detector.detect_faces(image)

        for det in detections:
            # 4. Extract face crop
            crop = Preprocessor.extract_face_crop(image, det.box)

            # 5. Assess quality
            quality = self.recognizer.assess_quality(crop)

            if not quality.is_usable:
                # Poor quality face -> route to INSUFFICIENT_EVIDENCE (Never absent)
                evidence = FaceEvidence(
                    frame_id=frame.id,
                    box_x1=det.box[0],
                    box_y1=det.box[1],
                    box_x2=det.box[2],
                    box_y2=det.box[3],
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    evidence_state=EvidenceState.INSUFFICIENT_EVIDENCE,
                    reason_code=quality.reason_code,
                    model_artifact_hash=det.detector_model_hash,
                )
                db.add(evidence)
                continue

            # 6. Extract embedding (P0-E: 5-landmark aligned SFace embedding)
            if det.raw_face is not None:
                try:
                    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    emb = self.recognizer.align_and_compute_embedding(cv_img, det.raw_face)
                except Exception:
                    emb = self.recognizer.compute_embedding(crop)
            else:
                emb = self.recognizer.compute_embedding(crop)

            # 7. Exact roster 1:N search
            candidate = self.recognizer.search_exact_roster(
                query_vector=emb.vector,
                enrolled_profiles=roster_gallery,
                match_threshold=0.45,
                margin_threshold=0.10,
            )

            # 8. Active PAD liveness security gate
            sec = self.pad.verify_liveness(crop, mandatory=True, threshold=0.85)
            if sec.status == "FAIL":
                evidence = FaceEvidence(
                    frame_id=frame.id,
                    box_x1=det.box[0],
                    box_y1=det.box[1],
                    box_x2=det.box[2],
                    box_y2=det.box[3],
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    candidate_student_id=candidate.student_id if candidate.is_matched else None,
                    similarity_score=candidate.similarity_score,
                    score_margin=candidate.margin_to_second,
                    evidence_state=EvidenceState.SECURITY_FAIL,
                    reason_code="PAD_SPOOF_DETECTED",
                    model_artifact_hash=emb.recognizer_model_hash,
                )
                db.add(evidence)
                continue

            # 9. Classify evidence state
            if candidate.is_matched:
                state = EvidenceState.CANDIDATE
            elif candidate.reason_code == "AMBIGUOUS_LOOKALIKE_CONFLICT":
                state = EvidenceState.REVIEW
            else:
                state = EvidenceState.UNKNOWN

            evidence = FaceEvidence(
                frame_id=frame.id,
                box_x1=det.box[0],
                box_y1=det.box[1],
                box_x2=det.box[2],
                box_y2=det.box[3],
                detection_score=det.score,
                quality_score=quality.score,
                quality_reason=quality.reason_code,
                candidate_student_id=candidate.student_id if (candidate.is_matched or state == EvidenceState.REVIEW) else None,
                similarity_score=candidate.similarity_score,
                score_margin=candidate.margin_to_second,
                evidence_state=state,
                reason_code=candidate.reason_code,
                model_artifact_hash=emb.recognizer_model_hash,
            )
            db.add(evidence)

        # 10. Update frame and session status
        frame.status = "PROCESSED"
        if session.state in [SessionState.ROSTER_FROZEN, SessionState.CAPTURING, SessionState.PROCESSING]:
            session.state = SessionState.IN_REVIEW

        db.flush()


def run_worker_loop(worker_id: str | None = None, poll_interval_seconds: float = 2.0):
    """
    Continuous queue processing daemon for VisionWorker.
    Handles graceful termination on SIGINT/SIGTERM.
    Leases and executes vision inference jobs.
    """
    import signal
    import sys
    import time
    import uuid
    from datetime import datetime, timezone
    from app.core.database import SessionLocal
    from app.services.queue_service import QueueService

    worker_id = worker_id or f"vision-worker-{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting FRS Vision Worker [{worker_id}]...")

    worker = VisionWorker(worker_id=worker_id)
    running = True

    def handle_signal(sig, frame):
        nonlocal running
        logger.warning(f"Received termination signal ({sig}). Initiating graceful worker shutdown...")
        running = False

    try:
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    except (ValueError, AttributeError):
        # When running in threads or environments where signal handling is restricted
        pass

    logger.info(f"Vision Worker [{worker_id}] initialized. Listening for queued capture frames...")

    while running:
        db = SessionLocal()
        try:
            claimed_jobs = QueueService.claim_jobs(db, worker_id=worker_id, limit=5)
            if claimed_jobs:
                db.commit()
                for job in claimed_jobs:
                    if not running:
                        break
                    logger.info(f"Processing vision job {job.id} (type={job.job_type.value}, frame={job.frame_id})...")
                    try:
                        worker.process_job(db, job)
                        db.commit()
                        logger.info(f"Job {job.id} SUCCEEDED.")
                    except Exception as exc:
                        db.rollback()
                        logger.error(f"Job {job.id} FAILED: {exc}")
                        QueueService.record_job_failure(db, job.id, str(exc), retryable=True)
                        db.commit()
            else:
                db.close()
                time.sleep(poll_interval_seconds)
        except Exception as exc:
            db.rollback()
            logger.error(f"Worker queue polling error: {exc}")
            time.sleep(poll_interval_seconds)
        finally:
            try:
                db.close()
            except Exception:
                pass

    logger.info(f"Vision Worker [{worker_id}] stopped cleanly.")


if __name__ == "__main__":
    run_worker_loop()
