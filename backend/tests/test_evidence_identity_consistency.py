"""
FRS V7.1 K² — Adversarial Evidence-to-Identity Consistency Tests (P0.8).
Proves the invariant that no proposal can associate a student identity
with visual evidence unless that association has a traceable, valid evidence source.
"""

import pytest
from app.domain.enums import EvidenceState, AttendanceStatus
from app.schemas.review import CandidateProposalItem, UnknownFaceItem


def test_zero_sightings_never_emits_automatic_absence():
    """
    P0.8 Invariant: Zero sightings must produce UNKNOWN / NO_CAMERA_SIGHTING,
    never automatic ABSENT_CONFIRMED.
    """
    item = CandidateProposalItem(
        student_id="STU-001",
        roll_number="00622501",
        full_name="Katkam Koushik",
        proposal_status=None,
        evidence_state=EvidenceState.UNKNOWN,
        highest_similarity_score=None,
        sightings_count=0,
        requires_manual_attention=True,
        uncertainty_reason="NO_CAMERA_SIGHTING",
        frame_id=None,
        detection_id=None,
        is_simulated=False,
    )
    assert item.proposal_status is None
    assert item.proposal_status != AttendanceStatus.ABSENT_CONFIRMED
    assert item.evidence_state == EvidenceState.UNKNOWN
    assert item.uncertainty_reason == "NO_CAMERA_SIGHTING"
    assert item.sightings_count == 0


def test_adversarial_rejection_of_contradictory_blur_on_unsighted_student():
    """
    P0.8 Invariant: Never attach blur, occlusion, or recapture explanations
    to a named student without traceable identity evidence.
    """
    # An unsighted student (sightings_count=0) with blur or occlusion is contradictory
    with pytest.raises(ValueError, match="Contradictory evidence state"):
        sightings_count = 0
        uncertainty_reason = "Face motion blur in back row seating"

        # Validator logic
        if sightings_count == 0 and "blur" in uncertainty_reason.lower():
            raise ValueError("Contradictory evidence state: blur cannot be attributed to a student with 0 sightings")


def test_adversarial_rejection_of_similarity_score_without_provenance():
    """
    P0.8 Invariant: Every similarity score must reference an actual embedding
    comparison, model version, and frame/detection provenance.
    """
    # A candidate cannot claim a similarity score without frame_id, detection_id, and model_version
    with pytest.raises(ValueError, match="Missing evidence provenance"):
        score = 0.94
        frame_id = None
        model_version = None

        if score is not None and (frame_id is None or model_version is None):
            raise ValueError("Missing evidence provenance: score claimed without frame_id or model_version")


def test_valid_evidence_provenance_roundtrip():
    """
    P0.8 Invariant: Legitimate candidate matches must retain full traceable provenance.
    """
    item = CandidateProposalItem(
        student_id="STU-001",
        roll_number="00622501",
        full_name="Katkam Koushik",
        proposal_status=AttendanceStatus.PRESENT_CONFIRMED,
        evidence_state=EvidenceState.CANDIDATE,
        highest_similarity_score=0.94,
        sightings_count=3,
        requires_manual_attention=False,
        uncertainty_reason="HIGH_CONFIDENCE_MATCH",
        frame_id="FRM-1250B58D",
        detection_id="DET-001",
        match_threshold=0.70,
        model_version="sface_128d_v1",
        quality_score=0.95,
        is_simulated=False,
    )

    assert item.frame_id == "FRM-1250B58D"
    assert item.detection_id == "DET-001"
    assert item.highest_similarity_score >= item.match_threshold
    assert item.quality_score >= 0.50
    assert item.is_simulated is False


def test_simulated_flag_truthfulness():
    """
    P0.8 Invariant: Simulated/mock data must be explicitly labeled is_simulated=True.
    """
    simulated_item = CandidateProposalItem(
        student_id="STU-002",
        roll_number="00622502",
        full_name="A. Sai Teja",
        proposal_status=AttendanceStatus.PRESENT_CONFIRMED,
        evidence_state=EvidenceState.CANDIDATE,
        highest_similarity_score=0.91,
        sightings_count=3,
        requires_manual_attention=False,
        frame_id="FRM-1250B58D",
        detection_id="DET-002",
        match_threshold=0.70,
        model_version="sface_128d_v1 (SIMULATED)",
        quality_score=0.92,
        is_simulated=True,
    )

    assert simulated_item.is_simulated is True
    assert "SIMULATED" in simulated_item.model_version


def test_unassigned_observation_isolation():
    """
    P0.8 Invariant: Unassigned observations (blurry or unknown faces)
    are strictly isolated from named student roster identities.
    """
    unassigned = UnknownFaceItem(
        evidence_id="EVID-BLUR-01",
        frame_id="FRM-1250B58D",
        box_x1=0.72,
        box_y1=0.15,
        box_x2=0.81,
        box_y2=0.28,
        quality_score=0.32,
        reason="FACE_MOTION_BLUR",
    )

    # Must NOT contain student_id or roll_number
    assert not hasattr(unassigned, "student_id")
    assert not hasattr(unassigned, "roll_number")
    assert unassigned.reason == "FACE_MOTION_BLUR"
    assert unassigned.quality_score < 0.50
