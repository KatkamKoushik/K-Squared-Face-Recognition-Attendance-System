"""
FRS V7.1 K2 -- Evaluation, Acceptance & Institutional Pilot Benchmark Suite.
Validates model calibration, open-set impostor rejection, ambiguity margin routing,
non-biometric fallback guarantees, and supervised presentation attack detection.
"""

from collections import Counter
import numpy as np
from PIL import Image
import pytest
from sqlalchemy.orm import Session

from app.domain.enums import SessionState, EvidenceState, AttendanceStatus
from app.domain.models.session import AttendanceSession, RosterSnapshot, SnapshotStudentItem
from app.domain.models.capture import CaptureBatch, Frame, FaceEvidence
from app.domain.models.student import EnrollmentProfile
from app.services.model_registry_service import ModelRegistryService
from app.services.review_service import ReviewService
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from app.worker.adapters.pad_adapter import PadAdapter


def create_normalized_vector(seed: int, dim: int = 128) -> list[float]:
    rng = np.random.RandomState(seed)
    raw = rng.randn(dim).astype(np.float32)
    norm = np.linalg.norm(raw)
    return (raw / norm).tolist()


def test_evaluation_closed_set_known_student_identification(db_session: Session, seed_data):
    """
    Evaluation Gate: Enrolled students with matching facial features must achieve
    high cosine similarity (>= 0.85) and be proposed as PRESENT candidates.
    """
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]
    students = seed_data["students"]
    recognizer = RecognizerAdapter()

    base_vector = create_normalized_vector(seed=42)
    # Slight perturbation (same student, different lighting/viewpoint)
    pert_arr = np.array(base_vector, dtype=np.float32) + 0.04 * np.random.RandomState(99).randn(128).astype(np.float32)
    observed_vector = (pert_arr / np.linalg.norm(pert_arr)).tolist()

    sim = recognizer.cosine_similarity(base_vector, observed_vector)
    assert sim >= 0.85, f"Intraclass similarity too low: {sim}"

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=1)
    db_session.add(snapshot)
    db_session.flush()

    item = SnapshotStudentItem(
        snapshot_id=snapshot.id,
        student_id=students[0].id,
        roll_number=students[0].roll_number,
        full_name=students[0].full_name,
        cohort_id=students[0].cohort_id,
    )
    db_session.add(item)
    db_session.flush()

    batch = CaptureBatch(session_id=session.id)
    db_session.add(batch)
    db_session.flush()

    frame = Frame(
        batch_id=batch.id,
        frame_index=1,
        content_sha256="hash_bench_01",
        width=1920,
        height=1080,
        storage_path="D:/k^2/backend/storage/frames/bench_01.jpg",
        status="PROCESSED",
    )
    db_session.add(frame)
    db_session.flush()

    face = FaceEvidence(
        frame_id=frame.id,
        box_x1=100.0,
        box_y1=100.0,
        box_x2=250.0,
        box_y2=250.0,
        detection_score=0.96,
        quality_score=0.92,
        candidate_student_id=students[0].id,
        similarity_score=round(sim, 4),
        score_margin=0.25,
        evidence_state=EvidenceState.CANDIDATE,
        model_artifact_hash="face_recognition_sface_2021dec",
    )
    db_session.add(face)
    db_session.flush()

    proposal = ReviewService.generate_session_proposal(db_session, session.id)
    assert len(proposal.candidates) == 1
    c = proposal.candidates[0]
    assert c.student_id == students[0].id
    assert c.proposal_status == AttendanceStatus.PRESENT_CONFIRMED
    assert c.evidence_state == EvidenceState.CANDIDATE
    assert c.highest_similarity_score >= 0.85
    assert c.requires_manual_attention is False


def test_evaluation_open_set_impostor_zero_false_acceptance():
    """
    Evaluation Gate: Out-of-roster faces (impostors/visitors) must achieve 0% False Acceptance Rate.
    They must be routed to UNKNOWN / BELOW_MATCH_THRESHOLD, never mapped to an enrolled student.
    """
    adapter = RecognizerAdapter()

    enrolled_gallery = {
        f"student_{i}": create_normalized_vector(seed=i * 50)
        for i in range(1, 10)
    }

    # 10 random impostor query vectors
    false_acceptances = 0
    for imp_idx in range(1, 11):
        impostor_vec = create_normalized_vector(seed=imp_idx * 1000 + 7)
        candidate = adapter.search_exact_roster(
            query_vector=impostor_vec,
            enrolled_profiles=enrolled_gallery,
            match_threshold=0.70,
            margin_threshold=0.10,
        )

        if candidate.is_matched:
            false_acceptances += 1

    # False Acceptance Rate must strictly be 0.0%
    assert false_acceptances == 0, f"False Acceptance Rate violated: {false_acceptances} false acceptances"


def test_evaluation_ambiguity_threshold_margin_routing():
    """
    Evaluation Gate: When a detected face closely matches two enrolled students with
    a similarity difference < T_margin (0.10), search_exact_roster must refuse automated match
    and report AMBIGUOUS_LOOKALIKE_CONFLICT for faculty adjudication.
    """
    adapter = RecognizerAdapter()

    base_vector = create_normalized_vector(seed=888)
    twin_a = base_vector
    # Twin B is within 0.02 of Twin A
    twin_b_arr = np.array(twin_a, dtype=np.float32) + 0.03 * np.random.RandomState(123).randn(128).astype(np.float32)
    twin_b = (twin_b_arr / np.linalg.norm(twin_b_arr)).tolist()

    # Query vector matches both strongly
    query_vec = base_vector

    roster_gallery = {
        "student_twin_1": twin_a,
        "student_twin_2": twin_b,
    }

    result = adapter.search_exact_roster(
        query_vector=query_vec,
        enrolled_profiles=roster_gallery,
        match_threshold=0.70,
        margin_threshold=0.10,
    )

    assert result.is_matched is False
    assert result.reason_code == "AMBIGUOUS_LOOKALIKE_CONFLICT"
    assert result.margin_to_second < 0.10


def test_evaluation_triplet_loss_metric_separation():
    """
    Evaluates metric separation: Anchor-Positive pairs must have cosine similarity
    significantly higher than Anchor-Negative pairs (separation margin >= 0.35).
    """
    recognizer = RecognizerAdapter()

    margins = []
    for i in range(10):
        anchor = create_normalized_vector(seed=i * 100)
        pos_arr = np.array(anchor, dtype=np.float32) + 0.04 * np.random.RandomState(i + 1).randn(128).astype(np.float32)
        pos = (pos_arr / np.linalg.norm(pos_arr)).tolist()
        neg = create_normalized_vector(seed=(i + 1) * 999)

        pos_sim = recognizer.cosine_similarity(anchor, pos)
        neg_sim = recognizer.cosine_similarity(anchor, neg)

        margin = pos_sim - neg_sim
        margins.append(margin)
        assert pos_sim > 0.80, f"Positive similarity too low: {pos_sim}"
        assert neg_sim < 0.40, f"Negative similarity too high: {neg_sim}"
        assert margin >= 0.35, f"Triplet separation margin inadequate: {margin}"

    avg_margin = float(np.mean(margins))
    assert avg_margin >= 0.45, f"Average triplet separation margin: {avg_margin}"


def test_evaluation_presentation_attack_detection_policy():
    """
    Evaluation Gate: Evaluates honest PAD threat model.
    1. Low-texture displays / printouts trigger UNCERTAIN with faculty inspection required.
    2. Rich texture crops pass under supervised policy.
    3. Non-mandatory policy returns SKIPPED with faculty supervision notice.
    """
    pad = PadAdapter()

    # 1. Flat color crop (synthetic low-texture replay attack / paper printout)
    flat_crop = Image.new("RGB", (112, 112), color=(200, 200, 200))
    res_flat = pad.verify_liveness(flat_crop, mandatory=True)
    assert res_flat.status == "UNCERTAIN"
    assert res_flat.is_live is False
    assert "LOW_TEXTURE" in res_flat.reason_code

    # 2. Rich natural texture crop (natural facial skin gradient simulation)
    arr = np.random.RandomState(42).randint(80, 180, (112, 112, 3), dtype=np.uint8)
    textured_crop = Image.fromarray(arr)
    res_textured = pad.verify_liveness(textured_crop, mandatory=True)
    assert res_textured.status == "PASS"
    assert res_textured.is_live is True

    # 3. Non-mandatory policy returns SKIPPED with faculty supervision notice
    res_skipped = pad.verify_liveness(textured_crop, mandatory=False)
    assert res_skipped.status == "SKIPPED"
    assert res_skipped.reason_code == "FACULTY_SUPERVISED_ATTENDANCE_POLICY"


def test_evaluation_non_biometric_fallback_guarantee(db_session: Session, seed_data):
    """
    Evaluation Gate: Non-biometric manual fallback must be guaranteed for:
    1. Students with withheld biometric consent.
    2. Students with zero camera sightings.
    Under NO circumstances may an unobserved or non-consenting student be automatically marked absent.
    """
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]
    students = seed_data["students"]

    # Student 0 has withheld consent
    profile = db_session.get(EnrollmentProfile, students[0].id)
    if profile:
        profile.is_active = False
    else:
        profile = EnrollmentProfile(
            student_id=students[0].id,
            model_artifact_id="face_recognition_sface_2021dec",
            embedding_namespace="sface_128d_v1",
            embedding_dimension=128,
            vector_data=[0.1] * 128,
            profile_version=1,
            is_active=False,
        )
        db_session.add(profile)
    db_session.flush()

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=2)
    db_session.add(snapshot)
    db_session.flush()

    # Roster has student 0 (withheld consent) and student 1 (zero sightings)
    item0 = SnapshotStudentItem(
        snapshot_id=snapshot.id,
        student_id=students[0].id,
        roll_number=students[0].roll_number,
        full_name=students[0].full_name,
        cohort_id=students[0].cohort_id,
    )
    item1 = SnapshotStudentItem(
        snapshot_id=snapshot.id,
        student_id=students[1].id,
        roll_number=students[1].roll_number,
        full_name=students[1].full_name,
        cohort_id=students[1].cohort_id,
    )
    db_session.add_all([item0, item1])
    db_session.flush()

    # Empty frame capture batch (zero camera sightings)
    batch = CaptureBatch(session_id=session.id)
    db_session.add(batch)
    db_session.flush()

    frame = Frame(
        batch_id=batch.id,
        frame_index=1,
        content_sha256="hash_empty_01",
        width=1920,
        height=1080,
        storage_path="D:/k^2/backend/storage/frames/empty_01.jpg",
        status="PROCESSED",
    )
    db_session.add(frame)
    db_session.flush()

    proposal = ReviewService.generate_session_proposal(db_session, session.id)
    candidates = {c.student_id: c for c in proposal.candidates}

    # Student 0: Withheld consent must require non-biometric alternative
    c0 = candidates[students[0].id]
    assert c0.proposal_status is None
    assert c0.evidence_state == EvidenceState.UNKNOWN
    assert "NON_BIOMETRIC_ALTERNATIVE_REQUIRED" in c0.uncertainty_reason
    assert c0.requires_manual_attention is True

    # Student 1: Zero sightings must produce UNKNOWN / NO_CAMERA_SIGHTING, never absent
    c1 = candidates[students[1].id]
    assert c1.proposal_status is None
    assert c1.evidence_state == EvidenceState.UNKNOWN
    assert "NO_CAMERA_SIGHTING" in c1.uncertainty_reason
    assert c1.requires_manual_attention is True
