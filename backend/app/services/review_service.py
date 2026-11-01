"""
FRS V7.1 K² — Cross-Photo Reconciliation & Faculty Proposal Review Service.
Consolidates sightings across multi-photo batches, enforces open-set uncertainty separation.
"""

from typing import List, Dict, Set
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
            low_quality_faces = [f for f in frame.faces if f.quality_score < 0.5]
            if len(low_quality_faces) > 3:
                recapture_hints.append(
                    RecaptureHint(
                        frame_id=frame.id,
                        issue="HIGH_BLUR_OR_LOW_CONTRAST",
                        recommendation="Consider capturing an additional photo from a closer angle with stable lighting.",
                    )
                )

            for face in frame.faces:
                if face.evidence_state == EvidenceState.CANDIDATE and face.candidate_student_id:
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
                            quality_score=face.quality_score,
                            reason=face.reason_code,
                        )
                    )

        candidate_proposals: List[CandidateProposalItem] = []
        proposed_present_count = 0
        uncertain_count = 0

        for roster_student in roster_items:
            student_id = roster_student.student_id
            sightings = sightings_by_student.get(student_id, [])

            if sightings:
                best_sighting = max(sightings, key=lambda s: s.similarity_score or 0.0)
                highest_sim = best_sighting.similarity_score or 0.0
                has_margin_issue = any((s.score_margin or 1.0) < 0.08 for s in sightings)

                if has_margin_issue:
                    proposal_status = None
                    evidence_state = EvidenceState.REVIEW
                    requires_manual = True
                    reason = "LOW_MARGIN_AMBIGUOUS_CANDIDATE"
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
                        requires_manual_attention=requires_manual,
                        uncertainty_reason=reason,
                        frame_id=best_sighting.frame_id,
                        detection_id=best_sighting.id,
                        match_threshold=0.70,
                        model_version=best_sighting.model_artifact_hash,
                        quality_score=round(best_sighting.quality_score, 4) if best_sighting.quality_score is not None else None,
                        is_simulated=best_sighting.model_artifact_hash == "baseline_mock" or "mock" in best_sighting.model_artifact_hash.lower(),
                    )
                )
            else:
                # FRS P0.8 Invariant: Zero sightings must produce UNKNOWN / NO_CAMERA_SIGHTING, never automatic absence.
                # Blur/quality explanations must NEVER be attributed to an unsighted student.
                candidate_proposals.append(
                    CandidateProposalItem(
                        student_id=student_id,
                        roll_number=roster_student.roll_number,
                        full_name=roster_student.full_name,
                        proposal_status=None,
                        evidence_state=EvidenceState.UNKNOWN,
                        highest_similarity_score=None,
                        sightings_count=0,
                        requires_manual_attention=True,
                        uncertainty_reason="NO_CAMERA_SIGHTING",
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
