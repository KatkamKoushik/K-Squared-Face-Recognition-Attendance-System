"""
FRS V7.1 K² — Universal Demo Testing & Ground-Truth Analysis Service.
Executes real YuNet detection, 5-landmark alignment, and SFace 128-D embedding matching
against all registered students in the database, with zero branch or cohort restrictions.
"""

import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.student import Student, EnrollmentProfile, EnrollmentSubmission
from app.domain.enums import EnrollmentSubmissionStatus
from app.services.storage_service import CloudinaryStorageService
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from app.worker.preprocessor import Preprocessor
from app.schemas.demo import (
    DemoFaceBox,
    DemoStudentResult,
    DemoEnrolledStudentSummary,
    DemoAnalysisResponse,
)


class DemoService:
    @staticmethod
    def _pil_to_base64_jpeg(pil_img: Image.Image, quality: int = 90) -> str:
        """Encodes PIL Image into a base64 JPEG data URI."""
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=quality)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    @staticmethod
    def _create_fallback_avatar(name: str, roll_number: str) -> str:
        """Generates a clean institutional avatar image with initials when disk photo is missing."""
        img = Image.new("RGB", (128, 128), color=(30, 41, 59))  # Slate dark
        draw = ImageDraw.Draw(img)
        initials = "".join([part[0] for part in name.split() if part][:2]).upper() or roll_number[:2]
        # Draw circle background
        draw.ellipse([8, 8, 120, 120], fill=(51, 65, 85), outline=(99, 102, 241), width=2)
        # Approximate centered text
        draw.text((44, 48), initials, fill=(248, 250, 252))
        return DemoService._pil_to_base64_jpeg(img)

    @staticmethod
    def _load_reference_photo_base64(photo_path: Optional[str], full_name: str, roll_number: str) -> str:
        """Loads and crops the student reference portrait from Cloudinary or disk into base64 thumbnail."""
        if photo_path:
            try:
                raw_bytes = CloudinaryStorageService.load_image_bytes(photo_path)
                ref_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                ref_img.thumbnail((160, 160))
                return DemoService._pil_to_base64_jpeg(ref_img, quality=85)
            except Exception:
                pass
        return DemoService._create_fallback_avatar(full_name, roll_number)

    @staticmethod
    def list_enrolled_demo_students(db: Session) -> List[DemoEnrolledStudentSummary]:
        """Lists all enrolled students with active face profiles in the database."""
        stmt = (
            select(Student, EnrollmentSubmission.photo_storage_path)
            .join(EnrollmentProfile, Student.id == EnrollmentProfile.student_id)
            .outerjoin(
                EnrollmentSubmission,
                (Student.roll_number == EnrollmentSubmission.roll_number)
                & (EnrollmentSubmission.status == EnrollmentSubmissionStatus.APPROVED),
            )
            .where(Student.is_active == True, EnrollmentProfile.is_active == True)
            .order_by(Student.roll_number)
        )
        rows = db.execute(stmt).all()
        seen_ids = set()
        results: List[DemoEnrolledStudentSummary] = []
        for student, photo_path in rows:
            if student.id in seen_ids:
                continue
            seen_ids.add(student.id)
            results.append(
                DemoEnrolledStudentSummary(
                    student_id=student.id,
                    roll_number=student.roll_number,
                    full_name=student.full_name,
                    is_active=student.is_active,
                    has_reference_photo=bool(photo_path and (photo_path.startswith("http") or os.path.exists(photo_path))),
                    photo_url=photo_path if (photo_path and (photo_path.startswith("http://") or photo_path.startswith("https://"))) else None,
                )
            )
        return results

    @staticmethod
    def analyze_demo_photo(
        db: Session,
        image_bytes: bytes,
        match_threshold: float = 0.363,
        margin_threshold: float = 0.10,
        blur_threshold: float = 50.0,
    ) -> DemoAnalysisResponse:
        """
        Processes a group or individual classroom photograph for ground-truth inspection:
        1. Detects all faces using OpenCV Zoo YuNet ONNX.
        2. Assesses per-face image quality (Laplacian variance and size).
        3. Extracts 128-D SFace embeddings with 5-landmark alignment.
        4. Matches against ALL enrolled student profiles in PostgreSQL.
        5. Computes attendance breakdown: Granted, Not Granted (Absent), and Unidentified Strangers.
        """
        # 1. Decode image
        try:
            pil_raw = Image.open(io.BytesIO(image_bytes))
            pil_raw.verify()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Uploaded file is not a valid decoded image: {exc}") from exc

        w, h = image.size
        if w < 64 or h < 64:
            raise ValueError(f"Image resolution too low ({w}x{h} px).")

        # 2. Fetch all enrolled gallery vectors and metadata
        stmt = (
            select(Student, EnrollmentProfile, EnrollmentSubmission.photo_storage_path)
            .join(EnrollmentProfile, Student.id == EnrollmentProfile.student_id)
            .outerjoin(
                EnrollmentSubmission,
                (Student.roll_number == EnrollmentSubmission.roll_number)
                & (EnrollmentSubmission.status == EnrollmentSubmissionStatus.APPROVED),
            )
            .where(Student.is_active == True, EnrollmentProfile.is_active == True)
        )
        enrolled_rows = db.execute(stmt).all()

        enrolled_gallery: Dict[str, List[float]] = {}
        student_metadata: Dict[str, Dict[str, Any]] = {}

        for student, profile, photo_path in enrolled_rows:
            if profile.vector_data and len(profile.vector_data) == 128:
                enrolled_gallery[student.id] = profile.vector_data
                student_metadata[student.id] = {
                    "roll_number": student.roll_number,
                    "full_name": student.full_name,
                    "photo_path": photo_path,
                }

        # 3. Detect faces with YuNet
        detector = DetectorAdapter(strict_mode=True)
        recognizer = RecognizerAdapter(strict_mode=True)
        cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        detections = detector.detect_faces(image)

        # Pass 1: Extract all embeddings and evaluate candidate matches individually
        extracted_faces: List[Dict[str, Any]] = []
        for idx, det in enumerate(detections, start=1):
            crop = Preprocessor.extract_face_crop(image, det.box)
            crop_base64 = DemoService._pil_to_base64_jpeg(crop, quality=85)
            quality = recognizer.assess_quality(crop, min_variance=blur_threshold, min_size=24)

            if not quality.is_usable:
                extracted_faces.append({
                    "idx": idx,
                    "det": det,
                    "quality": quality,
                    "crop_base64": crop_base64,
                    "is_quality_usable": False,
                    "candidate": None,
                })
                continue

            if det.raw_face is not None:
                try:
                    emb = recognizer.align_and_compute_embedding(cv_img, det.raw_face)
                except Exception:
                    emb = recognizer.compute_embedding(crop)
            else:
                emb = recognizer.compute_embedding(crop)

            candidate = recognizer.search_exact_roster(
                query_vector=emb.vector,
                enrolled_profiles=enrolled_gallery,
                match_threshold=match_threshold,
                margin_threshold=margin_threshold,
            )

            extracted_faces.append({
                "idx": idx,
                "det": det,
                "quality": quality,
                "crop_base64": crop_base64,
                "is_quality_usable": True,
                "candidate": candidate,
            })

        # Pass 2: Mutual Exclusivity - A single physical student identity can only be assigned to AT MOST ONE face.
        # Find which student_ids are claimed by multiple faces, and award the identity to the HIGHEST similarity face.
        claimed_students: Dict[str, List[int]] = {}
        for f_idx, item in enumerate(extracted_faces):
            if item["is_quality_usable"] and item["candidate"] and item["candidate"].is_matched:
                claimed_students.setdefault(item["candidate"].student_id, []).append(f_idx)

        winning_faces: set = set()
        duplicate_conflicts: Dict[int, Tuple[str, float, float]] = {}

        for s_id, face_indices in claimed_students.items():
            face_indices.sort(key=lambda i: extracted_faces[i]["candidate"].similarity_score, reverse=True)
            winner_idx = face_indices[0]
            winning_faces.add(winner_idx)
            winner_score = extracted_faces[winner_idx]["candidate"].similarity_score

            for duplicate_idx in face_indices[1:]:
                dup_score = extracted_faces[duplicate_idx]["candidate"].similarity_score
                duplicate_conflicts[duplicate_idx] = (s_id, dup_score, winner_score)

        # Pass 3: Build face boxes with duplicate conflicts cleanly marked
        detected_boxes: List[DemoFaceBox] = []
        matched_student_ids: Dict[str, Tuple[float, str]] = {}
        unidentified_boxes: List[DemoFaceBox] = []

        for f_idx, item in enumerate(extracted_faces):
            idx = item["idx"]
            det = item["det"]
            quality = item["quality"]
            crop_base64 = item["crop_base64"]

            if not item["is_quality_usable"]:
                face_box = DemoFaceBox(
                    face_index=idx,
                    box=det.box,
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    face_crop_base64=crop_base64,
                    status="QUALITY_REJECTED",
                    attendance_granted=False,
                    similarity_score=0.0,
                    margin=0.0,
                    color_hex="#6B7280",  # Slate gray
                    badge_label=f"Low Quality ({quality.reason_code})",
                )
                detected_boxes.append(face_box)
                unidentified_boxes.append(face_box)
                continue

            candidate = item["candidate"]

            if f_idx in winning_faces and candidate.student_id in student_metadata:
                s_meta = student_metadata[candidate.student_id]
                ref_b64 = DemoService._load_reference_photo_base64(
                    s_meta["photo_path"], s_meta["full_name"], s_meta["roll_number"]
                )
                face_box = DemoFaceBox(
                    face_index=idx,
                    box=det.box,
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    face_crop_base64=crop_base64,
                    status="MATCHED",
                    attendance_granted=True,
                    student_id=candidate.student_id,
                    roll_number=s_meta["roll_number"],
                    full_name=s_meta["full_name"],
                    similarity_score=candidate.similarity_score,
                    margin=candidate.margin_to_second,
                    reference_photo_base64=ref_b64,
                    color_hex="#10B981",  # Emerald green
                    badge_label=f"{s_meta['full_name']} ({s_meta['roll_number']})",
                )
                detected_boxes.append(face_box)
                matched_student_ids[candidate.student_id] = (candidate.similarity_score, crop_base64)

            elif f_idx in duplicate_conflicts:
                s_id, dup_sim, best_sim = duplicate_conflicts[f_idx]
                s_meta = student_metadata.get(s_id, {})
                face_box = DemoFaceBox(
                    face_index=idx,
                    box=det.box,
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    face_crop_base64=crop_base64,
                    status="DUPLICATE_CONFLICT",
                    attendance_granted=False,
                    student_id=s_id,
                    roll_number=s_meta.get("roll_number"),
                    full_name=s_meta.get("full_name"),
                    similarity_score=dup_sim,
                    margin=candidate.margin_to_second,
                    color_hex="#F59E0B",  # Amber orange
                    badge_label=f"Duplicate Match: {s_meta.get('full_name', s_id)} (Sim: {dup_sim:.3f} < {best_sim:.3f})",
                )
                detected_boxes.append(face_box)
                unidentified_boxes.append(face_box)

            elif candidate.reason_code == "AMBIGUOUS_LOOKALIKE_CONFLICT":
                s_meta = student_metadata.get(candidate.student_id, {})
                face_box = DemoFaceBox(
                    face_index=idx,
                    box=det.box,
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    face_crop_base64=crop_base64,
                    status="AMBIGUOUS",
                    attendance_granted=False,
                    student_id=candidate.student_id,
                    roll_number=s_meta.get("roll_number"),
                    full_name=s_meta.get("full_name"),
                    similarity_score=candidate.similarity_score,
                    margin=candidate.margin_to_second,
                    color_hex="#F59E0B",  # Amber orange
                    badge_label=f"Ambiguous Lookalike (Margin < {margin_threshold})",
                )
                detected_boxes.append(face_box)
                unidentified_boxes.append(face_box)

            else:
                # UNKNOWN_VISITOR (Stranger / not in database)
                face_box = DemoFaceBox(
                    face_index=idx,
                    box=det.box,
                    detection_score=det.score,
                    quality_score=quality.score,
                    quality_reason=quality.reason_code,
                    face_crop_base64=crop_base64,
                    status="UNKNOWN_VISITOR",
                    attendance_granted=False,
                    similarity_score=candidate.similarity_score,
                    margin=candidate.margin_to_second,
                    color_hex="#EF4444",  # Ruby red
                    badge_label=f"Unknown Visitor (Sim: {candidate.similarity_score:.3f} < {match_threshold})",
                )
                detected_boxes.append(face_box)
                unidentified_boxes.append(face_box)

        # 4. Group into Attendance Granted vs Not Granted (Absent)
        attendance_granted_list: List[DemoStudentResult] = []
        attendance_not_granted_list: List[DemoStudentResult] = []

        for s_id, s_meta in student_metadata.items():
            ref_b64 = DemoService._load_reference_photo_base64(
                s_meta["photo_path"], s_meta["full_name"], s_meta["roll_number"]
            )
            if s_id in matched_student_ids:
                best_score, crop_b64 = matched_student_ids[s_id]
                attendance_granted_list.append(
                    DemoStudentResult(
                        student_id=s_id,
                        roll_number=s_meta["roll_number"],
                        full_name=s_meta["full_name"],
                        attendance_granted=True,
                        status="PRESENT",
                        similarity_score=best_score,
                        face_crop_base64=crop_b64,
                        reference_photo_base64=ref_b64,
                    )
                )
            else:
                attendance_not_granted_list.append(
                    DemoStudentResult(
                        student_id=s_id,
                        roll_number=s_meta["roll_number"],
                        full_name=s_meta["full_name"],
                        attendance_granted=False,
                        status="ABSENT",
                        similarity_score=None,
                        face_crop_base64=None,
                        reference_photo_base64=ref_b64,
                    )
                )

        # Sort lists predictably by roll number
        attendance_granted_list.sort(key=lambda s: s.roll_number)
        attendance_not_granted_list.sort(key=lambda s: s.roll_number)

        return DemoAnalysisResponse(
            total_detected_faces=len(detections),
            total_enrolled_students=len(student_metadata),
            present_count=len(attendance_granted_list),
            absent_count=len(attendance_not_granted_list),
            unknown_count=len(unidentified_boxes),
            detected_faces=detected_boxes,
            attendance_granted=attendance_granted_list,
            attendance_not_granted=attendance_not_granted_list,
            unidentified_faces=unidentified_boxes,
        )

