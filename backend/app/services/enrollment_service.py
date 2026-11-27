"""
K² FRS — Student Biometric Enrollment Service.
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
from PIL import Image, ImageOps
Image.MAX_IMAGE_PIXELS = None
import cv2
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ResourceNotFoundError, StateTransitionError, ConflictError
from app.domain.enums import EnrollmentSubmissionStatus, AuditAction, SessionState, StudentLifecycleStatus
from app.domain.models.academic import Cohort, Department
from app.domain.models.audit import AuditEvent
from app.domain.models.student import Student, EnrollmentProfile, EnrollmentSubmission
from app.domain.models.session import AttendanceSession
from app.schemas.enrollment import EnrollmentSubmissionCreate
from app.schemas.events import EventMessage, RealtimeEventType
from app.services.event_broadcaster import broadcaster
from app.services.storage_service import CloudinaryStorageService
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from app.worker.adapters.arcface_adapter import SCRFD500MDetector, ArcFaceMobileNetRecognizer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EnrollmentService:

    @staticmethod
    def _compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _select_primary_face(detections: List[Any]) -> Any:
        """
        Selects the primary subject face from candidate detections by evaluating
        bounding box area, frame centrality, and detection confidence.
        Guarantees robust enrollment when background bystanders, shadows, or classroom peers are present.
        """
        if not detections:
            raise ValueError("No human face detected.")
        if len(detections) == 1:
            return detections[0]

        def _rank_face(d: Any) -> float:
            bw = max(0.0, d.box[2] - d.box[0])
            bh = max(0.0, d.box[3] - d.box[1])
            area = bw * bh
            cx = (d.box[0] + d.box[2]) / 2.0
            cy = (d.box[1] + d.box[3]) / 2.0
            dist_from_center = ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) ** 0.5
            centrality_weight = max(0.2, 1.0 - dist_from_center)
            score = max(0.1, float(d.score))
            # Prominence prioritizes large, centered, high-confidence faces
            return area * centrality_weight * (score ** 0.5)

        return max(detections, key=_rank_face)

    @staticmethod
    def _select_primary_face_scrfd(boxes: np.ndarray, scores: np.ndarray, kpss: np.ndarray, img_shape: tuple) -> int:
        """Select primary subject face from SCRFD candidate detections."""
        if len(boxes) == 1:
            return 0
        h, w = img_shape[:2]
        best_idx = 0
        max_rank = -1.0
        for i in range(len(boxes)):
            bw = boxes[i, 2] - boxes[i, 0]
            bh = boxes[i, 3] - boxes[i, 1]
            area = max(0.0, bw * bh)
            cx = (boxes[i, 0] + boxes[i, 2]) / (2.0 * w)
            cy = (boxes[i, 1] + boxes[i, 3]) / (2.0 * h)
            dist = np.sqrt((cx - 0.5) ** 2 + (cy - 0.5) ** 2)
            centrality = max(0.2, 1.0 - dist)
            score = max(0.1, float(scores[i]))
            rank = area * centrality * (score ** 0.5)
            if rank > max_rank:
                max_rank = rank
                best_idx = i
        return best_idx

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

        # Duplicate check in approved submissions
        existing_approved = db.execute(
            select(EnrollmentSubmission).where(
                EnrollmentSubmission.roll_number == data.roll_number.strip().upper(),
                EnrollmentSubmission.status == EnrollmentSubmissionStatus.APPROVED,
            )
        ).scalar_one_or_none()
        if existing_approved:
            raise ConflictError(
                resource="EnrollmentSubmission",
                identifier=data.roll_number,
                message=f"Student with roll number {data.roll_number} has already been approved and registered.",
            )

        # 2. Size and dimension limits
        if len(file_bytes) > 50 * 1024 * 1024:
            raise ValueError("Uploaded portrait exceeds maximum allowable size of 50MB.")

        try:
            pil_raw = Image.open(io.BytesIO(file_bytes))
            pil_raw.verify()  # Verify image integrity
            # Re-open after verify()
            pil_img = Image.open(io.BytesIO(file_bytes))
        except Exception as exc:
            raise ValueError(f"Uploaded file is not a valid decoded image: {exc}") from exc

        # Transpose according to EXIF orientation (fixes rotated smartphone camera photos)
        try:
            from PIL import ImageOps
            pil_img = ImageOps.exif_transpose(pil_img) or pil_img
        except Exception:
            pass

        w, h = pil_img.size
        if w < 100 or h < 100:
            raise ValueError(f"Image resolution too low ({w}x{h} px). Minimum required resolution is 100x100 px.")

        # Auto-rescale high-resolution smartphone portraits (e.g., 2016x4480) down to max 2560px
        MAX_DIMENSION = 2560
        if w > MAX_DIMENSION or h > MAX_DIMENSION:
            pil_img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            w, h = pil_img.size

        # 3. Strip EXIF & GPS metadata by creating fresh RGB buffer
        clean_img = Image.new("RGB", (w, h))
        clean_img.paste(pil_img.convert("RGB"))

        # 4. Strict YuNet Face Detection
        detector = DetectorAdapter(strict_mode=True)
        detections = detector.detect_faces(clean_img)
        if len(detections) == 0:
            raise ValueError("No human face detected in the submitted photograph. Please provide a clear, well-lit frontal portrait.")

        # Identify the primary student face (eliminates rejections caused by background bystanders or peers)
        primary_det = EnrollmentService._select_primary_face(detections)

        # When bystanders or multiple faces are present, isolate the student's portrait with portrait margins
        if len(detections) > 1:
            x1, y1, x2, y2 = primary_det.box
            pad_x = (x2 - x1) * 0.5
            pad_top = (y2 - y1) * 0.6
            pad_bottom = (y2 - y1) * 0.8
            crop_x1 = max(0, int((x1 - pad_x) * w))
            crop_y1 = max(0, int((y1 - pad_top) * h))
            crop_x2 = min(w, int((x2 + pad_x) * w))
            crop_y2 = min(h, int((y2 + pad_bottom) * h))
            if crop_x2 - crop_x1 >= 100 and crop_y2 - crop_y1 >= 100:
                clean_img = clean_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))

        # 5. Save stripped JPEG to Cloudinary object storage (with local fallback)
        buf = io.BytesIO()
        clean_img.save(buf, format="JPEG", quality=95)
        clean_bytes = buf.getvalue()

        photo_storage_url = CloudinaryStorageService.upload_enrollment_portrait(
            file_bytes=clean_bytes,
            roll_number=data.roll_number,
        )

        photo_sha256 = EnrollmentService._compute_sha256(clean_bytes)

        # Resolve cohort if not provided but department and year match
        cohort_id = data.cohort_id
        if not cohort_id:
            cohort_match = db.execute(
                select(Cohort.id).where(Cohort.name.ilike(f"%{data.department.strip()}%"))
            ).scalars().first()
            if not cohort_match:
                cohort_match = db.execute(select(Cohort.id)).scalars().first()
            cohort_id = cohort_match

        # Check if an existing pending or recapture submission exists to update
        existing_sub = db.execute(
            select(EnrollmentSubmission).where(
                EnrollmentSubmission.roll_number == data.roll_number.strip().upper(),
                EnrollmentSubmission.status.in_([
                    EnrollmentSubmissionStatus.PENDING_REVIEW,
                    EnrollmentSubmissionStatus.RECAPTURE_REQUIRED,
                ]),
            )
        ).scalar_one_or_none()

        if existing_sub:
            existing_sub.full_name = data.full_name.strip()
            existing_sub.institutional_email = str(data.institutional_email).strip().lower()
            existing_sub.department = data.department.strip().upper()
            existing_sub.academic_year = data.academic_year.strip()
            existing_sub.cohort_id = cohort_id
            existing_sub.photo_storage_path = photo_storage_url
            existing_sub.photo_sha256 = photo_sha256
            existing_sub.photo_mime = "image/jpeg"
            existing_sub.status = EnrollmentSubmissionStatus.PENDING_REVIEW
            existing_sub.rejection_reason = None
            submission = existing_sub
        else:
            submission = EnrollmentSubmission(
                roll_number=data.roll_number.strip().upper(),
                full_name=data.full_name.strip(),
                institutional_email=str(data.institutional_email).strip().lower(),
                department=data.department.strip().upper(),
                academic_year=data.academic_year.strip(),
                cohort_id=cohort_id,
                photo_storage_path=photo_storage_url,
                photo_sha256=photo_sha256,
                photo_mime="image/jpeg",
                status=EnrollmentSubmissionStatus.PENDING_REVIEW,
                consent_acknowledged=True,
            )
            db.add(submission)
        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ENROLLMENT_SUBMITTED,
                channel="global:admin",
                payload={
                    "submission_id": submission.id,
                    "roll_number": submission.roll_number,
                    "full_name": submission.full_name,
                    "department": submission.department,
                },
            ),
            db=db,
        )
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
        department_code: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> List[EnrollmentSubmission]:
        stmt = select(EnrollmentSubmission)
        if department_id or department_code:
            from app.domain.models.academic import Cohort
            dept_conditions = []
            if department_code:
                dept_conditions.append(EnrollmentSubmission.department.ilike(department_code.strip()))
            if department_id:
                dept_cohort_ids = select(Cohort.id).where(Cohort.department_id == department_id)
                dept_conditions.append(EnrollmentSubmission.cohort_id.in_(dept_cohort_ids))
            stmt = stmt.where(or_(*dept_conditions))
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
            current_val = sub.status.value if hasattr(sub.status, "value") else str(sub.status)
            raise StateTransitionError(
                message=f"Cannot approve submission in state {current_val}",
                current_state=current_val,
                attempted_state="APPROVED",
                reason_code="ILLEGAL_SUBMISSION_TRANSITION",
            )

        try:
            image_bytes = CloudinaryStorageService.load_image_bytes(sub.photo_storage_path)
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise FileNotFoundError(f"Stored enrollment portrait cannot be loaded from {sub.photo_storage_path}: {e}")
        w, h = pil_img.size

        # 2. Strict face detection & landmark localization
        detector = DetectorAdapter(strict_mode=True)
        detections = detector.detect_faces(pil_img)
        if not detections:
            raise RuntimeError("Cannot approve: No face detected in stored portrait.")

        best_det = EnrollmentService._select_primary_face(detections)

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

        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ENROLLMENT_DECIDED,
                channel="global:admin",
                payload={"submission_id": sub.id, "status": "APPROVED", "roll_number": sub.roll_number},
            ),
            db=db,
        )
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

        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ENROLLMENT_DECIDED,
                channel="global:admin",
                payload={"submission_id": sub.id, "status": "REJECTED", "roll_number": sub.roll_number, "reason": sub.rejection_reason},
            ),
            db=db,
        )
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

        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ENROLLMENT_DECIDED,
                channel="global:admin",
                payload={"submission_id": sub.id, "status": "RECAPTURE_REQUIRED", "roll_number": sub.roll_number, "reason": sub.rejection_reason},
            ),
            db=db,
        )
        db.commit()
        db.refresh(sub)

        return sub

    @staticmethod
    def direct_enroll_student(
        db: Session,
        roll_number: str,
        full_name: str,
        department: str,
        academic_year: Optional[str] = "2023-2027",
        institutional_email: Optional[str] = None,
        cohort_id: Optional[str] = None,
        file_bytes: bytes = b"",
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Direct mobile student biometric enrollment for RMX5003.
        Bypasses two-step staging review:
        1. Validates and normalizes uploaded portrait face image.
        2. Uploads portrait directly to Cloudinary (folder: k2_frs/enrollments).
        3. Creates/activates Student and approved EnrollmentSubmission records.
        4. Extracts and persists multi-model embeddings for ALL models separately:
           - Option 1 (512-D ArcFace MobileFaceNet, namespace: mobilefacenet_512d_v1)
           - Option 3 (128-D OpenCV Zoo SFace, namespace: sface_128d_v1)
           - Fine-Tuned (128-D KUCET Fine-Tuned SFace, namespace: kucet_frs_sface_finetuned_v2)
        5. Commits and broadcasts approval event.
        """
        clean_roll = roll_number.strip().upper()
        clean_name = full_name.strip()
        clean_dept = department.strip().upper()
        clean_year = (academic_year or "2023-2027").strip()
        clean_email = (institutional_email or f"{clean_roll.lower()}@kucet.ac.in").strip().lower()

        if not clean_roll or len(clean_roll) < 3:
            raise ValueError("Valid student roll number is required (min 3 characters).")
        if not clean_name or len(clean_name) < 2:
            raise ValueError("Valid student full name is required.")
        if not clean_dept:
            raise ValueError("Valid department code is required.")
        if not file_bytes or len(file_bytes) < 1000:
            raise ValueError("Student portrait photo file is empty or corrupted.")
        if len(file_bytes) > 50 * 1024 * 1024:
            raise ValueError("Uploaded portrait exceeds maximum allowable size of 50MB.")

        # 1. Decode image and normalize orientation
        try:
            pil_raw = Image.open(io.BytesIO(file_bytes))
            pil_raw.verify()
            pil_img = Image.open(io.BytesIO(file_bytes))
            pil_img = ImageOps.exif_transpose(pil_img).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Uploaded photo is not a valid decodable image: {exc}")

        w, h = pil_img.size
        if w < 64 or h < 64:
            raise ValueError(f"Image resolution too low ({w}x{h} px). Frontal portrait required.")

        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # 2. Detect face using SCRFD and YuNet
        scrfd = SCRFD500MDetector()
        boxes, scores, kpss, _ = scrfd.detect(cv_img, target_size=640, score_thresh=0.25)
        if len(boxes) == 0:
            boxes, scores, kpss, _ = scrfd.detect(cv_img, target_size=1280, score_thresh=0.20)

        yunet = DetectorAdapter(strict_mode=True)
        yunet_dets = yunet.detect_faces(pil_img)

        if len(boxes) == 0 and len(yunet_dets) == 0:
            raise ValueError("No human face detected in portrait. Ensure a clear, upright frontal portrait.")

        # 3. Upload photo to Cloudinary
        cloudinary_url = CloudinaryStorageService.upload_enrollment_portrait(
            file_bytes=file_bytes,
            roll_number=clean_roll,
        )
        photo_sha256 = hashlib.sha256(file_bytes).hexdigest()

        # 4. Resolve Cohort
        assigned_cohort_id = cohort_id
        if not assigned_cohort_id:
            cohort_match = db.execute(
                select(Cohort)
                .join(Department, Cohort.department_id == Department.id)
                .where(Department.code.ilike(clean_dept))
            ).scalars().first()
            if cohort_match:
                assigned_cohort_id = cohort_match.id
            else:
                fallback_cohort = db.execute(select(Cohort)).scalars().first()
                assigned_cohort_id = fallback_cohort.id if fallback_cohort else str(uuid.uuid4())

        # 5. Create or update Student record
        student = db.execute(
            select(Student).where(Student.roll_number == clean_roll)
        ).scalar_one_or_none()

        if not student:
            student = Student(
                roll_number=clean_roll,
                full_name=clean_name,
                institutional_email=clean_email,
                cohort_id=assigned_cohort_id,
                is_active=True,
                lifecycle_status=StudentLifecycleStatus.ACTIVE,
            )
            db.add(student)
            db.flush()
        else:
            student.full_name = clean_name
            student.is_active = True
            student.lifecycle_status = StudentLifecycleStatus.ACTIVE
            if clean_email:
                student.institutional_email = clean_email
            if assigned_cohort_id:
                student.cohort_id = assigned_cohort_id
            db.flush()

        # 6. Create or update EnrollmentSubmission record
        sub = db.execute(
            select(EnrollmentSubmission).where(EnrollmentSubmission.roll_number == clean_roll)
        ).scalar_one_or_none()

        if sub:
            sub.full_name = clean_name
            sub.institutional_email = clean_email
            sub.department = clean_dept
            sub.academic_year = clean_year
            sub.cohort_id = student.cohort_id
            sub.photo_storage_path = cloudinary_url
            sub.photo_sha256 = photo_sha256
            sub.photo_mime = "image/jpeg"
            sub.status = EnrollmentSubmissionStatus.APPROVED
            sub.consent_acknowledged = True
            sub.reviewed_at = utc_now()
            sub.reviewed_by_user_id = actor_id
            sub.rejection_reason = None
        else:
            sub = EnrollmentSubmission(
                roll_number=clean_roll,
                full_name=clean_name,
                institutional_email=clean_email,
                department=clean_dept,
                academic_year=clean_year,
                cohort_id=student.cohort_id,
                photo_storage_path=cloudinary_url,
                photo_sha256=photo_sha256,
                photo_mime="image/jpeg",
                status=EnrollmentSubmissionStatus.APPROVED,
                consent_acknowledged=True,
                reviewed_at=utc_now(),
                reviewed_by_user_id=actor_id,
            )
            db.add(sub)
        db.flush()

        # 7. Extract multi-model embeddings separately for all models
        models_enrolled: List[str] = []
        namespaces: List[str] = []

        def _upsert_profile(ns: str, model_hash: str, dim: int, vec: List[float]):
            existing_prof = db.execute(
                select(EnrollmentProfile).where(
                    EnrollmentProfile.student_id == student.id,
                    EnrollmentProfile.embedding_namespace == ns,
                )
            ).scalar_one_or_none()
            rounded_vec = [round(float(v), 6) for v in vec]
            if existing_prof:
                existing_prof.vector_data = rounded_vec
                existing_prof.model_artifact_id = model_hash
                existing_prof.embedding_dimension = dim
                existing_prof.is_active = True
                existing_prof.profile_version += 1
            else:
                new_prof = EnrollmentProfile(
                    student_id=student.id,
                    model_artifact_id=model_hash,
                    embedding_namespace=ns,
                    embedding_dimension=dim,
                    vector_data=rounded_vec,
                    profile_version=1,
                    is_active=True,
                )
                db.add(new_prof)

        # 7A. Option 1: SCRFD-500M + ArcFace MobileFaceNet (512-D)
        if len(boxes) > 0:
            best_kps_idx = EnrollmentService._select_primary_face_scrfd(boxes, scores, kpss, cv_img.shape)
            arcface = ArcFaceMobileNetRecognizer()
            opt1_emb = arcface.align_and_extract(cv_img, kpss[best_kps_idx])
            norm = float(np.linalg.norm(opt1_emb))
            if abs(norm - 1.0) > 1e-4:
                opt1_emb = opt1_emb / norm
            _upsert_profile(
                ns="mobilefacenet_512d_v1",
                model_hash="9cc6e4a75f0e2bf0b1aed94578f144d15175f357bdc05e815e5c4a02b319eb4f",
                dim=512,
                vec=opt1_emb.tolist(),
            )
            models_enrolled.append("Option 1 (512-D ArcFace)")
            namespaces.append("mobilefacenet_512d_v1")

        # 7B. Option 3: OpenCV Zoo SFace (128-D)
        primary_yunet = None
        if len(yunet_dets) > 0:
            primary_yunet = EnrollmentService._select_primary_face(yunet_dets)
            sface_zoo = RecognizerAdapter(strict_mode=False)
            opt3_emb = sface_zoo.align_and_compute_embedding(cv_img, primary_yunet.raw_face)
            _upsert_profile(
                ns="sface_128d_v1",
                model_hash="0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
                dim=128,
                vec=opt3_emb.vector,
            )
            models_enrolled.append("Option 3 (128-D SFace)")
            namespaces.append("sface_128d_v1")

        # 7C. Fine-Tuned: KUCET SFace Fine-Tuned (128-D)
        if primary_yunet is not None:
            ft_candidates = [
                Path(__file__).resolve().parent.parent.parent / "models" / "kucet_frs_sface_finetuned.onnx",
                Path("backend/models/kucet_frs_sface_finetuned.onnx").resolve(),
                Path("models/kucet_frs_sface_finetuned.onnx").resolve(),
            ]
            ft_path = next((p for p in ft_candidates if p.exists()), ft_candidates[0])
            sface_ft = RecognizerAdapter(model_path=ft_path, strict_mode=False)
            ft_emb = sface_ft.align_and_compute_embedding(cv_img, primary_yunet.raw_face)
            _upsert_profile(
                ns="kucet_frs_sface_finetuned_v2",
                model_hash="0d980b104c783bc4230b074d5b44b9bf329b6cc5d457ba92416b5d6b7000755f",
                dim=128,
                vec=ft_emb.vector,
            )
            models_enrolled.append("Fine-Tuned SFace (128-D)")
            namespaces.append("kucet_frs_sface_finetuned_v2")

        # 8. Commit and broadcast
        db.commit()
        db.refresh(student)
        db.refresh(sub)

        broadcaster.publish_sync(
            EventMessage(
                event_type=RealtimeEventType.ENROLLMENT_DECIDED,
                channel="global:admin",
                payload={
                    "student_id": student.id,
                    "roll_number": student.roll_number,
                    "full_name": student.full_name,
                    "department": clean_dept,
                    "status": "APPROVED",
                    "source": "MOBILE_DIRECT_ENROLL",
                },
            ),
            db=db,
        )

        return {
            "success": True,
            "message": f"Student {clean_name} ({clean_roll}) enrolled directly with Cloudinary storage and multi-model embeddings.",
            "student_id": student.id,
            "roll_number": student.roll_number,
            "full_name": student.full_name,
            "department": clean_dept,
            "cloudinary_photo_url": cloudinary_url,
            "models_enrolled": models_enrolled,
            "namespaces": namespaces,
        }


    @staticmethod
    def get_dashboard_stats(db: Session, department_id: Optional[str] = None) -> Dict[str, Any]:
        from datetime import date
        from app.domain.models.student import Student, EnrollmentSubmission
        from app.domain.models.academic import SubjectOffering, Department, Cohort, Subject, Faculty
        from app.domain.models.session import AttendanceSession, AttendanceUnit
        from app.domain.models.audit import CommitReceipt
        from app.domain.enums import EnrollmentSubmissionStatus, SessionState, UnitStatus
        from sqlalchemy import func, desc

        if department_id:
            dept = db.get(Department, department_id)
            dept_code = dept.code if dept else None
            dept_cohorts_sub = select(Cohort.id).where(Cohort.department_id == department_id)
            dept_subjects_sub = select(Subject.id).where(Subject.department_id == department_id)
            dept_offerings_sub = select(SubjectOffering.id).where(SubjectOffering.subject_id.in_(dept_subjects_sub))

            total_students = db.execute(
                select(func.count(Student.id)).where(Student.cohort_id.in_(dept_cohorts_sub))
            ).scalar() or 0
            total_offerings = db.execute(
                select(func.count(SubjectOffering.id)).where(SubjectOffering.subject_id.in_(dept_subjects_sub))
            ).scalar() or 0
            total_departments = 1 if dept else 0
            total_cohorts = db.execute(
                select(func.count(Cohort.id)).where(Cohort.department_id == department_id)
            ).scalar() or 0
            sub_stmt = select(func.count(EnrollmentSubmission.id)).where(
                EnrollmentSubmission.status == EnrollmentSubmissionStatus.PENDING_REVIEW
            )
            if dept_code:
                sub_stmt = sub_stmt.where(
                    or_(
                        EnrollmentSubmission.department.ilike(dept_code),
                        EnrollmentSubmission.cohort_id.in_(dept_cohorts_sub),
                    )
                )
            else:
                sub_stmt = sub_stmt.where(EnrollmentSubmission.cohort_id.in_(dept_cohorts_sub))
            pending_subs = db.execute(sub_stmt).scalar() or 0
            finalized_sessions = db.execute(
                select(func.count(AttendanceSession.id)).where(
                    AttendanceSession.state == SessionState.FINALIZED,
                    AttendanceSession.offering_id.in_(dept_offerings_sub),
                )
            ).scalar() or 0
            today = date.today()
            units_today = db.execute(
                select(func.count(AttendanceUnit.id))
                .join(AttendanceSession, AttendanceUnit.session_id == AttendanceSession.id)
                .where(
                    AttendanceSession.session_date == today,
                    AttendanceSession.offering_id.in_(dept_offerings_sub),
                    AttendanceUnit.is_conducted.is_(True),
                    AttendanceUnit.status.in_([UnitStatus.COMMITTED, UnitStatus.CONDUCTED_CONFIRMED]),
                )
            ).scalar() or 0
            recent_sessions_rows = db.execute(
                select(AttendanceSession)
                .where(
                    AttendanceSession.state == SessionState.FINALIZED,
                    AttendanceSession.offering_id.in_(dept_offerings_sub),
                )
                .order_by(desc(AttendanceSession.finalized_at))
                .limit(10)
            ).scalars().all()
        else:
            total_students = db.execute(select(func.count(Student.id))).scalar() or 0
            total_offerings = db.execute(select(func.count(SubjectOffering.id))).scalar() or 0
            total_departments = db.execute(select(func.count(Department.id))).scalar() or 0
            total_cohorts = db.execute(select(func.count(Cohort.id))).scalar() or 0
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

            today = date.today()
            units_today = db.execute(
                select(func.count(AttendanceUnit.id))
                .join(AttendanceSession, AttendanceUnit.session_id == AttendanceSession.id)
                .where(
                    AttendanceSession.session_date == today,
                    AttendanceUnit.is_conducted.is_(True),
                    AttendanceUnit.status.in_([UnitStatus.COMMITTED, UnitStatus.CONDUCTED_CONFIRMED]),
                )
            ).scalar() or 0

            recent_sessions_rows = db.execute(
                select(AttendanceSession)
                .where(AttendanceSession.state == SessionState.FINALIZED)
                .order_by(desc(AttendanceSession.finalized_at))
                .limit(10)
            ).scalars().all()

        recent_sessions = []
        for s in recent_sessions_rows:
            receipt = db.execute(
                select(CommitReceipt).where(CommitReceipt.session_id == s.id)
            ).scalars().first()

            offering = db.execute(
                select(SubjectOffering).where(SubjectOffering.id == s.offering_id)
            ).scalars().first()

            subject = db.execute(
                select(Subject).where(Subject.id == offering.subject_id)
            ).scalars().first() if offering else None

            cohort = db.execute(
                select(Cohort).where(Cohort.id == offering.primary_cohort_id)
            ).scalars().first() if offering else None

            faculty = db.execute(
                select(Faculty).where(Faculty.id == s.faculty_id)
            ).scalars().first()

            conducted_units = receipt.total_conducted_units if receipt else s.planned_units
            present_count = receipt.total_present_records if receipt else 0
            absent_count = receipt.total_absent_records if receipt else 0
            total_enrolled = present_count + absent_count
            pct = f"{(present_count / total_enrolled * 100):.1f}%" if total_enrolled > 0 else "0.0%"

            receipt_hash_display = (receipt.receipt_hash[:18] + "...") if receipt and len(receipt.receipt_hash) > 18 else (receipt.receipt_hash if receipt else "0x0000000000000000")
            ts_str = s.finalized_at.strftime("%b %d, %I:%M %p") if s.finalized_at else s.session_date.strftime("%b %d, %Y")

            recent_sessions.append({
                "session_id": s.id,
                "subject_code": subject.code if subject else "N/A",
                "subject_name": subject.name if subject else "Subject",
                "cohort": cohort.name if cohort else "Cohort",
                "faculty": faculty.full_name if faculty else "Faculty",
                "conducted_units": conducted_units,
                "present_count": present_count,
                "total_enrolled": total_enrolled,
                "attendance_percent": pct,
                "receipt_hash": receipt_hash_display,
                "timestamp": ts_str,
            })

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
            "conducted_units_today": units_today,
            "active_departments_count": total_departments,
            "active_cohorts_count": total_cohorts,
            "recent_sessions": recent_sessions,
            "system_readiness": readiness,
        }
