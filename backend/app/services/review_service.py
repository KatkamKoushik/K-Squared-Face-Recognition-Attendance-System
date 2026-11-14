"""
K² FRS — Cross-Photo Reconciliation & Faculty Proposal Review Service.
Consolidates sightings across multi-photo batches, enforces open-set uncertainty separation.
"""

from typing import List, Dict, Set
from collections import Counter
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, Session
from app.core.errors import ResourceNotFoundError
from app.domain.enums import EvidenceState, AttendanceStatus
from app.domain.models.session import AttendanceSession, RosterSnapshot
from app.domain.models.capture import CaptureBatch, Frame, FaceEvidence
from app.schemas.review import (
    CandidateProposalItem,
    UnknownFaceItem,
    RecaptureHint,
    SessionProposalReviewResponse,
)


class ReviewService:

    @staticmethod
    def generate_session_proposal(
        db: Session,
        session_id: str,
    ) -> SessionProposalReviewResponse:
        """
        Reconciles evidence across all frames for a session and produces a candidate
        proposal for faculty review. Does NOT finalize attendance or decide absence.
        """
        session_stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.snapshot).selectinload(RosterSnapshot.items)
            )
            .where(AttendanceSession.id == session_id)
        )
        session = db.execute(session_stmt).scalar_one_or_none()
        if not session or not session.snapshot:
            raise ResourceNotFoundError("Session/RosterSnapshot", session_id)

        roster_items = session.snapshot.items
        total_eligible = len(roster_items)

        frames_stmt = (
            select(Frame)
            .join(CaptureBatch, CaptureBatch.id == Frame.batch_id)
            .options(selectinload(Frame.faces))
            .where(CaptureBatch.session_id == session_id)
        )
        frames = list(db.execute(frames_stmt).scalars().all())

        sightings_by_student: Dict[str, List[FaceEvidence]] = {}
        unknown_faces: List[UnknownFaceItem] = []
        recapture_hints: List[RecaptureHint] = []

        for frame in frames:
            frame_faces = list(frame.faces)
            low_quality_faces = [f for f in frame_faces if f.quality_score is not None and f.quality_score < 0.5]
            if len(low_quality_faces) > 3 or (frame_faces and len(low_quality_faces) / len(frame_faces) > 0.4):
                recapture_hints.append(
                    RecaptureHint(
                        frame_id=frame.id,
                        issue="HIGH_BLUR_OR_LOW_CONTRAST",
                        recommendation="Frame has high blur or low illumination. Consider capturing an additional photo from a closer angle with stable lighting.",
                    )
                )

            for face in frame_faces:
                if (face.evidence_state in [EvidenceState.CANDIDATE, EvidenceState.REVIEW]) and face.candidate_student_id:
                    sightings_by_student.setdefault(face.candidate_student_id, []).append(face)
                elif face.evidence_state == EvidenceState.UNKNOWN:
                    unknown_faces.append(
                        UnknownFaceItem(
                            evidence_id=face.id,
                            frame_id=frame.id,
                            box_x1=face.box_x1,
                            box_y1=face.box_y1,
                            box_x2=face.box_x2,
                            box_y2=face.box_y2,
                            quality_score=face.quality_score or 0.0,
                            reason=face.reason_code,
                        )
                    )

        # Classroom coverage analysis across sweep
        if frames and total_eligible > 0 and len(frames) >= 2:
            if len(sightings_by_student) < (total_eligible * 0.50):
                recapture_hints.append(
                    RecaptureHint(
                        frame_id=frames[-1].id,
                        issue="LOW_CLASSROOM_COVERAGE",
                        recommendation=f"Only {len(sightings_by_student)} of {total_eligible} enrolled students detected across {len(frames)} photos. Capture additional wide-angle sweeps covering back rows and room corners.",
                    )
                )

        candidate_proposals: List[CandidateProposalItem] = []
        proposed_present_count = 0
        uncertain_count = 0

        from app.domain.models.student import EnrollmentProfile
        inactive_consent_ids = set(
            db.execute(
                select(EnrollmentProfile.student_id).where(
                    EnrollmentProfile.student_id.in_([r.student_id for r in roster_items]),
                    EnrollmentProfile.is_active == False,
                )
            ).scalars().all()
        )

        for roster_student in roster_items:
            student_id = roster_student.student_id
            sightings = sightings_by_student.get(student_id, [])

            if sightings:
                best_sighting = max(sightings, key=lambda s: (s.similarity_score or 0.0, s.quality_score or 0.0))
                highest_sim = best_sighting.similarity_score or 0.0
                best_margin = best_sighting.score_margin or 0.0
                sighted_frame_ids = sorted(list({s.frame_id for s in sightings if s.frame_id}))

                # Multi-photo conflict detection: multiple distinct faces in same frame claiming same identity
                frame_id_counts = Counter(s.frame_id for s in sightings if s.frame_id)
                has_same_frame_duplicate = any(count > 1 for count in frame_id_counts.values())

                if has_same_frame_duplicate:
                    proposal_status = None
                    evidence_state = EvidenceState.REVIEW
                    requires_manual = True
                    reason = "SAME_FRAME_MULTIPLE_DETECTIONS_CONFLICT"
                    uncertain_count += 1
                elif best_sighting.evidence_state == EvidenceState.REVIEW or best_margin < 0.10:
                    proposal_status = None
                    evidence_state = EvidenceState.REVIEW
                    requires_manual = True
                    reason = "LOW_MARGIN_AMBIGUOUS_CANDIDATE"
                    uncertain_count += 1
                elif highest_sim < 0.363:
                    proposal_status = None
                    evidence_state = EvidenceState.REVIEW
                    requires_manual = True
                    reason = "LOW_CONFIDENCE_BELOW_THRESHOLD"
                    uncertain_count += 1
                else:
                    proposal_status = AttendanceStatus.PRESENT_CONFIRMED
                    evidence_state = EvidenceState.CANDIDATE
                    requires_manual = False
                    reason = "HIGH_CONFIDENCE_MATCH"
                    proposed_present_count += 1

                candidate_proposals.append(
                    CandidateProposalItem(
                        student_id=student_id,
                        roll_number=roster_student.roll_number,
                        full_name=roster_student.full_name,
                        proposal_status=proposal_status,
                        evidence_state=evidence_state,
                        highest_similarity_score=round(highest_sim, 4),
                        sightings_count=len(sightings),
                        sighted_frame_ids=sighted_frame_ids,
                        requires_manual_attention=requires_manual,
                        uncertainty_reason=reason,
                        frame_id=best_sighting.frame_id,
                        detection_id=best_sighting.id,
                        match_threshold=0.363,
                        model_version=best_sighting.model_artifact_hash,
                        quality_score=round(best_sighting.quality_score, 4) if best_sighting.quality_score is not None else None,
                        is_simulated=best_sighting.model_artifact_hash == "baseline_mock" or "mock" in (best_sighting.model_artifact_hash or "").lower(),
                    )
                )
            else:
                # FRS P0.8 Invariant: Zero sightings must produce UNKNOWN / NO_CAMERA_SIGHTING, never automatic absence.
                # Blur/quality explanations must NEVER be attributed to an unsighted student.
                zero_sighting_reason = (
                    "NON_BIOMETRIC_ALTERNATIVE_REQUIRED (CONSENT WITHHELD)"
                    if (student_id in inactive_consent_ids)
                    else "NO_CAMERA_SIGHTING"
                )
                candidate_proposals.append(
                    CandidateProposalItem(
                        student_id=student_id,
                        roll_number=roster_student.roll_number,
                        full_name=roster_student.full_name,
                        proposal_status=None,
                        evidence_state=EvidenceState.UNKNOWN,
                        highest_similarity_score=None,
                        sightings_count=0,
                        sighted_frame_ids=[],
                        requires_manual_attention=True,
                        uncertainty_reason=zero_sighting_reason,
                        frame_id=None,
                        detection_id=None,
                        match_threshold=None,
                        model_version=None,
                        quality_score=None,
                        is_simulated=False,
                    )
                )

        proposed_absent_count = sum(1 for c in candidate_proposals if c.proposal_status == AttendanceStatus.ABSENT_CONFIRMED)

        return SessionProposalReviewResponse(
            session_id=session_id,
            total_eligible_students=total_eligible,
            proposed_present_count=proposed_present_count,
            proposed_absent_count=proposed_absent_count,
            uncertain_count=uncertain_count,
            unknown_faces_count=len(unknown_faces),
            candidates=candidate_proposals,
            unknown_faces=unknown_faces,
            recapture_hints=recapture_hints,
        )
