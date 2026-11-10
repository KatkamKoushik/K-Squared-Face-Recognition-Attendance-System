"""
FRS V7.1 K² — Student Biometric Enrollment Service.
Enforces strict lifecycle (PENDING_REVIEW -> APPROVED / REJECTED / RECAPTURE_REQUIRED),
private photo storage, and real YuNet detection & SFace 5-landmark embedding generation upon admin approval.
"""

from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid

import numpy as np
from PIL import Image
import cv2
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ResourceNotFoundError, StateTransitionError, ConflictError
from app.domain.enums import EnrollmentSubmissionStatus, AuditAction, SessionState
from app.domain.models.academic import Cohort
from app.domain.models.audit import AuditEvent
from app.domain.models.student import Student, EnrollmentProfile, EnrollmentSubmission
from app.domain.models.session import AttendanceSession
from app.schemas.enrollment import EnrollmentSubmissionCreate
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EnrollmentService:

    @staticmethod
    def _compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def submit_enrollment(
        db: Session,
        data: EnrollmentSubmissionCreate,
        file_bytes: bytes,
        mime_type: str,
    ) -> EnrollmentSubmission:
        """
        Public student submission path.
        Validates image, strips EXIF, performs YuNet face verification, and persists staged submission.
        """
        if not data.consent_acknowledged:
            raise ValueError("Biometric consent acknowledgement is mandatory for attendance enrollment.")

        # 1. Duplicate roll number check in existing active students
        existing_student = db.execute(
            select(Student).where(Student.roll_number == data.roll_number.strip().upper())
        ).scalar_one_or_none()
        if existing_student:
            raise ConflictError(
                resource="Student",
                identifier=data.roll_number,
                message=f"Student with roll number {data.roll_number} is already enrolled in the institution.",
            )

        # Duplicate check in pending submissions
        existing_sub = db.execute(
            select(EnrollmentSubmission).where(
                EnrollmentSubmission.roll_number == data.roll_number.strip().upper(),
                EnrollmentSubmission.status.in_([
                    EnrollmentSubmissionStatus.PENDING_REVIEW,
                    EnrollmentSubmissionStatus.APPROVED,
                ]),
            )
        ).scalar_one_or_none()
        if existing_sub:
            raise ConflictError(
                resource="EnrollmentSubmission",
                identifier=data.roll_number,
                message=f"An enrollment submission for roll number {data.roll_number} is already {existing_sub.status.value}.",
            )

        # 2. Size and dimension limits
        if len(file_bytes) > 10 * 1024 * 1024:
            raise ValueError("Uploaded portrait exceeds maximum allowable size of 10MB.")

        try:
            pil_raw = Image.open(io.BytesIO(file_bytes))
            pil_raw.verify()  # Verify image integrity
            # Re-open after verify()
            pil_img = Image.open(io.BytesIO(file_bytes))
        except Exception as exc:
            raise ValueError(f"Uploaded file is not a valid decoded image: {exc}") from exc

        w, h = pil_img.size
        if w < 160 or h < 160:
            raise ValueError(f"Image resolution too low ({w}x{h} px). Minimum required resolution is 160x160 px.")
        if w > 4096 or h > 4096:
            raise ValueError(f"Image resolution too high ({w}x{h} px). Maximum allowable resolution is 4096x4096 px.")

        # 3. Strip EXIF & GPS metadata by creating fresh RGB buffer
        clean_img = Image.new("RGB", (w, h))
        clean_img.paste(pil_img.convert("RGB"))

        # 4. Strict YuNet Face Detection
        detector = DetectorAdapter(strict_mode=True)
        detections = detector.detect_faces(clean_img)
        if len(detections) == 0:
            raise ValueError("No human face detected in the submitted photograph. Please provide a clear, well-lit frontal portrait.")
        if len(detections) > 1:
            raise ValueError(
                f"Multiple faces ({len(detections)}) detected. Enrollment portrait must contain only the student's face."
            )

        # 5. Save stripped JPEG to private access-controlled storage
        storage_base = Path(settings.STORAGE_DIR) / "enrollments"
        storage_base.mkdir(parents=True, exist_ok=True)
        storage_filename = f"enrollment_{uuid.uuid4().hex}.jpg"
        target_path = storage_base / storage_filename

        buf = io.BytesIO()
        clean_img.save(buf, format="JPEG", quality=95)
        clean_bytes = buf.getvalue()

        with open(target_path, "wb") as f:
            f.write(clean_bytes)

        photo_sha256 = EnrollmentService._compute_sha256(clean_bytes)

        # Resolve cohort if not provided but department and year match
        cohort_id = data.cohort_id
        if not cohort_id:
            cohort_match = db.execute(
                select(Cohort.id).where(Cohort.cohort_code.ilike(f"%{data.department.strip()}%"))
            ).scalars().first()
            if cohort_match:
                cohort_id = cohort_match

        submission = EnrollmentSubmission(
            roll_number=data.roll_number.strip().upper(),
            full_name=data.full_name.strip(),
            institutional_email=str(data.institutional_email).strip().lower(),
            department=data.department.strip().upper(),
            academic_year=data.academic_year.strip(),
            cohort_id=cohort_id,
            photo_storage_path=str(target_path.resolve()),
            photo_sha256=photo_sha256,
            photo_mime="image/jpeg",
            status=EnrollmentSubmissionStatus.PENDING_REVIEW,
            consent_acknowledged=True,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    @staticmethod
    def list_submissions(
        db: Session,
        status: Optional[EnrollmentSubmissionStatus] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EnrollmentSubmission]:
        stmt = select(EnrollmentSubmission)
        if status:
            stmt = stmt.where(EnrollmentSubmission.status == status)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    EnrollmentSubmission.roll_number.ilike(term),
                    EnrollmentSubmission.full_name.ilike(term),
                    EnrollmentSubmission.department.ilike(term),
                )
            )
        stmt = stmt.order_by(desc(EnrollmentSubmission.created_at)).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_submission_by_id(db: Session, submission_id: str) -> EnrollmentSubmission:
        sub = db.get(EnrollmentSubmission, submission_id)
        if not sub:
            raise ResourceNotFoundError("EnrollmentSubmission", submission_id)
        return sub

    @staticmethod
    def approve_submission(db: Session, submission_id: str, admin_user_id: str) -> EnrollmentSubmission:
        """
        Admin action: Approves student enrollment.
        Extracts real 5-landmark SFace embedding from stored portrait,
        creates/activates Student and EnrollmentProfile records, and promotes template to gallery.
        """
        sub = EnrollmentService.get_submission_by_id(db, submission_id)
        if sub.status not in [EnrollmentSubmissionStatus.PENDING_REVIEW, EnrollmentSubmissionStatus.RECAPTURE_REQUIRED]:
            raise StateTransitionError(
                message=f"Cannot approve submission in state {sub.status.value}",
                current_state=sub.status.value,
                attempted_state="APPROVED",
                reason_code="ILLEGAL_SUBMISSION_TRANSITION",
            )

        photo_path = Path(sub.photo_storage_path)
        if not photo_path.is_file():
            raise FileNotFoundError(f"Stored enrollment portrait missing at {photo_path}")

        # 1. Load clean image
        pil_img = Image.open(photo_path).convert("RGB")
        w, h = pil_img.size

        # 2. Strict face detection & landmark localization
        detector = DetectorAdapter(strict_mode=True)
        detections = detector.detect_faces(pil_img)
        if not detections:
            raise RuntimeError("Cannot approve: No face detected in stored portrait.")

        best_det = max(detections, key=lambda d: d.score)

        # 3. Strict 5-landmark SFace alignment & 128-D embedding extraction
        recognizer = RecognizerAdapter(strict_mode=True)
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        emb = recognizer.align_and_compute_embedding(cv_img, best_det.raw_face)

        # 4. Resolve or create Student record
        student = db.execute(
            select(Student).where(Student.roll_number == sub.roll_number)
        ).scalar_one_or_none()

        if not student:
            # Fallback cohort if unassigned
            cohort_id = sub.cohort_id
            if not cohort_id:
                any_cohort = db.execute(select(Cohort.id)).scalars().first()
                cohort_id = any_cohort or str(uuid.uuid4())

            student = Student(
                roll_number=sub.roll_number,
                institutional_email=sub.institutional_email,
                full_name=sub.full_name,
                cohort_id=cohort_id,
                is_active=True,
            )
            db.add(student)
            db.flush()

        # 5. Deactivate older profiles and insert new active EnrollmentProfile
        db.query(EnrollmentProfile).filter(
            EnrollmentProfile.student_id == student.id,
            EnrollmentProfile.embedding_namespace == emb.namespace,
        ).update({"is_active": False})

        profile = EnrollmentProfile(
            student_id=student.id,
            model_artifact_id=emb.recognizer_model_hash,
            embedding_namespace=emb.namespace,
            embedding_dimension=emb.dimension,
            vector_data=emb.vector,
            profile_version=1,
            is_active=True,
        )
        db.add(profile)

        # 6. Update Submission state
        sub.status = EnrollmentSubmissionStatus.APPROVED
        sub.reviewed_by_user_id = admin_user_id
        sub.reviewed_at = utc_now()
        sub.rejection_reason = None

        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def reject_submission(db: Session, submission_id: str, admin_user_id: str, reason: str) -> EnrollmentSubmission:
        sub = EnrollmentService.get_submission_by_id(db, submission_id)
        sub.status = EnrollmentSubmissionStatus.REJECTED
        sub.reviewed_by_user_id = admin_user_id
        sub.reviewed_at = utc_now()
        sub.rejection_reason = reason or "Administrative rejection based on enrollment guidelines."
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def request_recapture(db: Session, submission_id: str, admin_user_id: str, reason: str) -> EnrollmentSubmission:
        sub = EnrollmentService.get_submission_by_id(db, submission_id)
        sub.status = EnrollmentSubmissionStatus.RECAPTURE_REQUIRED
        sub.reviewed_by_user_id = admin_user_id
        sub.reviewed_at = utc_now()
        sub.rejection_reason = reason or "Photo quality inadequate. Frontal portrait recapture required."
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        total_students = db.execute(select(func.count(Student.id))).scalar() or 0
        from app.domain.models.academic import SubjectOffering
        total_offerings = db.execute(select(func.count(SubjectOffering.id))).scalar() or 0
        pending_subs = db.execute(
            select(func.count(EnrollmentSubmission.id)).where(
                EnrollmentSubmission.status == EnrollmentSubmissionStatus.PENDING_REVIEW
            )
        ).scalar() or 0
        finalized_sessions = db.execute(
            select(func.count(AttendanceSession.id)).where(
                AttendanceSession.state == SessionState.FINALIZED
            )
        ).scalar() or 0

        # Query recent finalized sessions
        recent_sessions_rows = db.execute(
            select(AttendanceSession)
            .where(AttendanceSession.state == SessionState.FINALIZED)
            .order_by(desc(AttendanceSession.finalized_at))
            .limit(5)
        ).scalars().all()

        recent_sessions = [
            {
                "session_id": s.id,
                "offering_id": s.offering_id,
                "finalized_at": s.finalized_at.isoformat() if s.finalized_at else None,
                "state": s.state.value,
            }
            for s in recent_sessions_rows
        ]

        # Verify model runtime readiness
        from app.worker.adapters.detector_adapter import DetectorAdapter
        from app.worker.adapters.recognizer_adapter import RecognizerAdapter
        try:
            det = DetectorAdapter(strict_mode=True)
            rec = RecognizerAdapter(strict_mode=True)
            readiness = "READY" if (det._detector is not None and rec._recognizer is not None) else "DEGRADED"
        except Exception:
            readiness = "DEGRADED"

        return {
            "total_enrolled_students": total_students,
            "total_active_offerings": total_offerings,
            "pending_submissions_count": pending_subs,
            "finalized_sessions_count": finalized_sessions,
            "recent_sessions": recent_sessions,
            "system_readiness": readiness,
        }
