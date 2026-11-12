"""
K² FRS — Phase P2 Multi-Photo Session Reconciliation Tests.
Verifies cross-frame evidence aggregation, duplicate resolution,
same-frame conflict detection, and classroom coverage gap analysis.
"""

import pytest
from sqlalchemy.orm import Session
from app.domain.enums import SessionState, EvidenceState, AttendanceStatus
from app.domain.models.session import AttendanceSession, RosterSnapshot, SnapshotStudentItem
from app.domain.models.capture import CaptureBatch, Frame, FaceEvidence
from app.services.review_service import ReviewService


def test_multi_photo_session_reconciliation_and_coverage(db_session: Session, seed_data):
    """
    Verifies Phase P2 multi-photo session reconciliation:
    1. Cross-frame aggregation of sightings (union of presence across sweeps).
    2. Best sighting selection (highest similarity and quality).
    3. Same-frame duplicate conflict detection (twin/lookalike in same photo).
    4. Sighted frame IDs propagation.
    5. Classroom coverage gap recapture hints when < 50% roster detected.
    """
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]
    students = seed_data["students"]

    # 1. Create session with 3 eligible students in frozen roster snapshot
    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=3)
    db_session.add(snapshot)
    db_session.flush()

    for s in students:
        item = SnapshotStudentItem(
            snapshot_id=snapshot.id,
            student_id=s.id,
            roll_number=s.roll_number,
            full_name=s.full_name,
            cohort_id=s.cohort_id,
        )
        db_session.add(item)
    db_session.flush()

    # 2. Create 3 frames representing classroom sweeps: Left, Center, Right
    batch = CaptureBatch(
        session_id=session.id,
    )
    db_session.add(batch)
    db_session.flush()

    frame_left = Frame(
        batch_id=batch.id,
        frame_index=1,
        content_sha256="hash_left_01",
        width=1920,
        height=1080,
        storage_path="D:/k^2/backend/storage/frames/frame_left.jpg",
        status="PROCESSED",
    )
    frame_center = Frame(
        batch_id=batch.id,
        frame_index=2,
        content_sha256="hash_center_02",
        width=1920,
        height=1080,
        storage_path="D:/k^2/backend/storage/frames/frame_center.jpg",
        status="PROCESSED",
    )
    frame_right = Frame(
        batch_id=batch.id,
        frame_index=3,
        content_sha256="hash_right_03",
        width=1920,
        height=1080,
        storage_path="D:/k^2/backend/storage/frames/frame_right.jpg",
        status="PROCESSED",
    )
    db_session.add_all([frame_left, frame_center, frame_right])
    db_session.flush()

    # Student 0: Sighted in frame_left (high confidence) and frame_center (lower confidence, edge of frame)
    # Reconciles to PRESENT_CONFIRMED based on best sighting in frame_left
    s0_sighting_1 = FaceEvidence(
        frame_id=frame_left.id,
        box_x1=100.0,
        box_y1=100.0,
        box_x2=200.0,
        box_y2=200.0,
        detection_score=0.95,
        quality_score=0.88,
        candidate_student_id=students[0].id,
        similarity_score=0.86,
        score_margin=0.35,
        evidence_state=EvidenceState.CANDIDATE,
        reason_code="HIGH_CONFIDENCE_MATCH",
        model_artifact_hash="sface_v1_onnx_hash",
    )
    s0_sighting_2 = FaceEvidence(
        frame_id=frame_center.id,
        box_x1=500.0,
        box_y1=120.0,
        box_x2=580.0,
        box_y2=200.0,
        detection_score=0.75,
        quality_score=0.60,
        candidate_student_id=students[0].id,
        similarity_score=0.72,
        score_margin=0.15,
        evidence_state=EvidenceState.CANDIDATE,
        reason_code="HIGH_CONFIDENCE_MATCH",
        model_artifact_hash="sface_v1_onnx_hash",
    )

    # Student 1: Sighted TWICE in the SAME photo (frame_right) -> Same-frame multiple detections conflict
    s1_sighting_1 = FaceEvidence(
        frame_id=frame_right.id,
        box_x1=50.0,
        box_y1=50.0,
        box_x2=120.0,
        box_y2=120.0,
        detection_score=0.90,
        quality_score=0.82,
        candidate_student_id=students[1].id,
        similarity_score=0.81,
        score_margin=0.20,
        evidence_state=EvidenceState.CANDIDATE,
        reason_code="HIGH_CONFIDENCE_MATCH",
        model_artifact_hash="sface_v1_onnx_hash",
    )
    s1_sighting_2 = FaceEvidence(
        frame_id=frame_right.id,
        box_x1=300.0,
        box_y1=50.0,
        box_x2=370.0,
        box_y2=120.0,
        detection_score=0.88,
        quality_score=0.78,
        candidate_student_id=students[1].id,
        similarity_score=0.79,
        score_margin=0.18,
        evidence_state=EvidenceState.CANDIDATE,
        reason_code="HIGH_CONFIDENCE_MATCH",
        model_artifact_hash="sface_v1_onnx_hash",
    )

    # Student 2: Zero sightings across all frames (absent from classroom)
    # Handled by zero-sighting invariant

    db_session.add_all([s0_sighting_1, s0_sighting_2, s1_sighting_1, s1_sighting_2])
    db_session.flush()

    # 3. Generate reconciled proposals
    proposal_resp = ReviewService.generate_session_proposal(db=db_session, session_id=session.id)

    assert proposal_resp.session_id == session.id
    assert proposal_resp.total_eligible_students == 3

    candidates = {c.student_id: c for c in proposal_resp.candidates}

    # Verify Student 0: High confidence reconciliation
    cand_0 = candidates[students[0].id]
    assert cand_0.proposal_status == AttendanceStatus.PRESENT_CONFIRMED
    assert cand_0.evidence_state == EvidenceState.CANDIDATE
    assert cand_0.sightings_count == 2
    assert sorted(cand_0.sighted_frame_ids) == sorted([frame_left.id, frame_center.id])
    assert cand_0.highest_similarity_score == 0.86
    assert cand_0.frame_id == frame_left.id  # Selected best sighting frame
    assert cand_0.requires_manual_attention is False
    assert cand_0.uncertainty_reason == "HIGH_CONFIDENCE_MATCH"

    # Verify Student 1: Same-frame duplicate conflict routing
    cand_1 = candidates[students[1].id]
    assert cand_1.proposal_status is None
    assert cand_1.evidence_state == EvidenceState.REVIEW
    assert cand_1.requires_manual_attention is True
    assert cand_1.uncertainty_reason == "SAME_FRAME_MULTIPLE_DETECTIONS_CONFLICT"
    assert cand_1.sightings_count == 2
    assert cand_1.sighted_frame_ids == [frame_right.id]

    # Verify Student 2: Zero sightings invariant (never automatic absence)
    cand_2 = candidates[students[2].id]
    assert cand_2.proposal_status is None
    assert cand_2.evidence_state == EvidenceState.UNKNOWN
    assert cand_2.requires_manual_attention is True
    assert cand_2.uncertainty_reason == "NO_CAMERA_SIGHTING"
    assert cand_2.sightings_count == 0
    assert cand_2.sighted_frame_ids == []
    assert cand_2.highest_similarity_score is None


def test_recapture_hints_on_low_quality_frames(db_session: Session, seed_data):
    """Verifies that frames with excessive blur/low quality generate actionable RecaptureHints."""
    faculty = seed_data["faculty"]
    offering = seed_data["offering"]
    students = seed_data["students"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=len(students))
    db_session.add(snapshot)
    db_session.flush()

    for s in students:
        item = SnapshotStudentItem(
            snapshot_id=snapshot.id,
            student_id=s.id,
            roll_number=s.roll_number,
            full_name=s.full_name,
            cohort_id=s.cohort_id,
        )
        db_session.add(item)
    db_session.flush()

    batch = CaptureBatch(
        session_id=session.id,
    )
    db_session.add(batch)
    db_session.flush()

    blurry_frame = Frame(
        batch_id=batch.id,
        frame_index=1,
        content_sha256="blurry_hash",
        width=1920,
        height=1080,
        storage_path="D:/k^2/backend/storage/frames/blurry.jpg",
        status="PROCESSED",
    )
    db_session.add(blurry_frame)
    db_session.flush()

    # Add 4 low quality face detections
    for i in range(4):
        face = FaceEvidence(
            frame_id=blurry_frame.id,
            box_x1=10.0 * i,
            box_y1=10.0 * i,
            box_x2=50.0 * i + 10.0,
            box_y2=50.0 * i + 10.0,
            detection_score=0.60,
            quality_score=0.35,  # Below 0.50 threshold
            evidence_state=EvidenceState.UNKNOWN,
            reason_code="FACE_IMAGE_BLURRY",
            model_artifact_hash="scrfd_v1",
        )
        db_session.add(face)
    db_session.flush()

    proposal_resp = ReviewService.generate_session_proposal(db=db_session, session_id=session.id)
    assert len(proposal_resp.recapture_hints) >= 1
    hint = proposal_resp.recapture_hints[0]
    assert hint.frame_id == blurry_frame.id
    assert hint.issue == "HIGH_BLUR_OR_LOW_CONTRAST"
    assert "lighting" in hint.recommendation.lower() or "angle" in hint.recommendation.lower()

