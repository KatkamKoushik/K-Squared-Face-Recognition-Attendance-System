"""
K² FRS — Multi-Photo Burst Sweep Fusion & Review Adjudication Test Suite.
Verifies cross-frame reconciliation, duplicate suppression, and 'no silent absence' invariants.
"""

import pytest
import uuid
from datetime import datetime, timezone

from app.domain.enums import SessionState, EvidenceState, AttendanceStatus, UserRole
from app.domain.models.academic import Department, Cohort, Subject, SubjectOffering, Faculty, User, AcademicYear, Term
from app.domain.models.student import Student, EnrollmentProfile
from app.domain.models.session import AttendanceSession, RosterSnapshot, SnapshotStudentItem
from app.domain.models.capture import CaptureBatch, Frame, FaceEvidence
from app.services.review_service import ReviewService


@pytest.fixture
def review_setup(db_session):
    # 1. Academic Hierarchy
    dept = Department(id=str(uuid.uuid4()), name="Civil Engineering", code="CIVIL-REV")
    cohort = Cohort(id=str(uuid.uuid4()), department_id=dept.id, name="Civil 2026", admission_year=2022, graduation_year=2026)
    subject = Subject(id=str(uuid.uuid4()), department_id=dept.id, code="CE-401", name="Structural Analysis")
    from datetime import date
    ay = AcademicYear(id=str(uuid.uuid4()), year_code="2026-2027", start_date=date(2026, 7, 1), end_date=date(2027, 5, 31), is_current=True)
    term = Term(id=str(uuid.uuid4()), academic_year_id=ay.id, term_type="ODD", start_date=date(2026, 7, 1), end_date=date(2026, 12, 31), is_active=True)
    offering = SubjectOffering(id=str(uuid.uuid4()), subject_id=subject.id, term_id=term.id, primary_cohort_id=cohort.id, section="A")
    
    faculty_user = User(id=str(uuid.uuid4()), email="fac_rev@kucet.ac.in", role=UserRole.FACULTY, hashed_password="pw")
    faculty = Faculty(id=str(uuid.uuid4()), user_id=faculty_user.id, department_id=dept.id, employee_id="EMP-REV-1", full_name="Dr. Review Faculty")

    # 2. Students: 3 enrolled students
    stu1 = Student(id=str(uuid.uuid4()), cohort_id=cohort.id, roll_number="26567T001", full_name="Student Left", institutional_email="stu1@kucet.ac.in")
    stu2 = Student(id=str(uuid.uuid4()), cohort_id=cohort.id, roll_number="26567T002", full_name="Student Center", institutional_email="stu2@kucet.ac.in")
    stu3 = Student(id=str(uuid.uuid4()), cohort_id=cohort.id, roll_number="26567T003", full_name="Student Right", institutional_email="stu3@kucet.ac.in")
    stu4 = Student(id=str(uuid.uuid4()), cohort_id=cohort.id, roll_number="26567T004", full_name="Student Absent", institutional_email="stu4@kucet.ac.in")

    # Enrollment Profiles
    ep1 = EnrollmentProfile(id=str(uuid.uuid4()), student_id=stu1.id, model_artifact_id="sface_128d", embedding_namespace="sface", embedding_dimension=128, vector_data=[0.1]*128, is_active=True)
    ep2 = EnrollmentProfile(id=str(uuid.uuid4()), student_id=stu2.id, model_artifact_id="sface_128d", embedding_namespace="sface", embedding_dimension=128, vector_data=[0.2]*128, is_active=True)
    ep3 = EnrollmentProfile(id=str(uuid.uuid4()), student_id=stu3.id, model_artifact_id="sface_128d", embedding_namespace="sface", embedding_dimension=128, vector_data=[0.3]*128, is_active=True)
    ep4 = EnrollmentProfile(id=str(uuid.uuid4()), student_id=stu4.id, model_artifact_id="sface_128d", embedding_namespace="sface", embedding_dimension=128, vector_data=[0.4]*128, is_active=True)

    db_session.add_all([dept, cohort, subject, ay, term, offering, faculty_user, faculty, stu1, stu2, stu3, stu4, ep1, ep2, ep3, ep4])
    db_session.flush()

    # 3. Session & Frozen Snapshot
    session = AttendanceSession(
        id=str(uuid.uuid4()),
        offering_id=offering.id,
        faculty_id=faculty.id,
        session_date=date(2026, 11, 14),
        state=SessionState.ROSTER_FROZEN,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(id=str(uuid.uuid4()), session_id=session.id, total_eligible_students=4)
    db_session.add(snapshot)
    db_session.flush()

    snap_items = [
        SnapshotStudentItem(snapshot_id=snapshot.id, student_id=stu1.id, roll_number="26567T001", full_name="Student Left", cohort_id=cohort.id),
        SnapshotStudentItem(snapshot_id=snapshot.id, student_id=stu2.id, roll_number="26567T002", full_name="Student Center", cohort_id=cohort.id),
        SnapshotStudentItem(snapshot_id=snapshot.id, student_id=stu3.id, roll_number="26567T003", full_name="Student Right", cohort_id=cohort.id),
        SnapshotStudentItem(snapshot_id=snapshot.id, student_id=stu4.id, roll_number="26567T004", full_name="Student Absent", cohort_id=cohort.id),
    ]
    db_session.add_all(snap_items)
    db_session.flush()

    return {
        "session": session,
        "stu1": stu1,
        "stu2": stu2,
        "stu3": stu3,
        "stu4": stu4,
        "faculty": faculty,
        "faculty_user": faculty_user,
    }


def test_multi_photo_burst_sweep_fusion_and_union(db_session, review_setup):
    session = review_setup["session"]
    stu1 = review_setup["stu1"]
    stu2 = review_setup["stu2"]
    stu3 = review_setup["stu3"]
    stu4 = review_setup["stu4"]

    # Create Batch with 2 Sweep Frames:
    # Frame 1: Left classroom angle (captures stu1 and stu2)
    # Frame 2: Right classroom angle (captures stu2 and stu3)
    batch = CaptureBatch(id=str(uuid.uuid4()), session_id=session.id)
    db_session.add(batch)
    db_session.flush()

    frame_left = Frame(
        id=str(uuid.uuid4()),
        batch_id=batch.id,
        frame_index=1,
        content_sha256="sha_frame_left",
        mime_type="image/jpeg",
        width=1920,
        height=1080,
        storage_path="frame_left.jpg",
    )
    frame_right = Frame(
        id=str(uuid.uuid4()),
        batch_id=batch.id,
        frame_index=2,
        content_sha256="sha_frame_right",
        mime_type="image/jpeg",
        width=1920,
        height=1080,
        storage_path="frame_right.jpg",
    )
    db_session.add_all([frame_left, frame_right])
    db_session.flush()

    # Evidence in Frame Left: stu1 @ 0.65, stu2 @ 0.50
    ev1_left = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame_left.id,
        box_x1=10, box_y1=10, box_x2=100, box_y2=100,
        detection_score=0.95,
        candidate_student_id=stu1.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.65,
        score_margin=0.25,
        quality_score=0.90,
        model_artifact_hash="sface_v1_approved",
    )
    ev2_left = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame_left.id,
        box_x1=110, box_y1=10, box_x2=200, box_y2=100,
        detection_score=0.95,
        candidate_student_id=stu2.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.50,
        score_margin=0.15,
        quality_score=0.85,
        model_artifact_hash="sface_v1_approved",
    )

    # Evidence in Frame Right: stu2 @ 0.75 (better angle in right sweep), stu3 @ 0.60
    ev2_right = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame_right.id,
        box_x1=10, box_y1=10, box_x2=100, box_y2=100,
        detection_score=0.95,
        candidate_student_id=stu2.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.75,
        score_margin=0.35,
        quality_score=0.95,
        model_artifact_hash="sface_v1_approved",
    )
    ev3_right = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame_right.id,
        box_x1=110, box_y1=10, box_x2=200, box_y2=100,
        detection_score=0.95,
        candidate_student_id=stu3.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.60,
        score_margin=0.20,
        quality_score=0.88,
        model_artifact_hash="sface_v1_approved",
    )

    db_session.add_all([ev1_left, ev2_left, ev2_right, ev3_right])
    db_session.commit()

    # Generate proposal
    proposal = ReviewService.generate_session_proposal(db_session, session.id)

    assert proposal.total_eligible_students == 4
    assert proposal.proposed_present_count == 3  # stu1, stu2, stu3 all verified
    assert proposal.uncertain_count == 0

    candidate_map = {c.student_id: c for c in proposal.candidates}

    # Verify stu1: detected in frame_left only
    assert candidate_map[stu1.id].proposal_status == AttendanceStatus.PRESENT_CONFIRMED
    assert candidate_map[stu1.id].highest_similarity_score == 0.65
    assert candidate_map[stu1.id].sightings_count == 1
    assert candidate_map[stu1.id].sighted_frame_ids == [frame_left.id]
    assert candidate_map[stu1.id].match_threshold == 0.363

    # Verify stu2: detected in BOTH frames, fused to higher score 0.75
    assert candidate_map[stu2.id].proposal_status == AttendanceStatus.PRESENT_CONFIRMED
    assert candidate_map[stu2.id].highest_similarity_score == 0.75
    assert candidate_map[stu2.id].sightings_count == 2
    assert sorted(candidate_map[stu2.id].sighted_frame_ids) == sorted([frame_left.id, frame_right.id])

    # Verify stu3: detected in frame_right only
    assert candidate_map[stu3.id].proposal_status == AttendanceStatus.PRESENT_CONFIRMED
    assert candidate_map[stu3.id].highest_similarity_score == 0.60
    assert candidate_map[stu3.id].sightings_count == 1
    assert candidate_map[stu3.id].sighted_frame_ids == [frame_right.id]

    # Verify stu4: No sightings -> NO_CAMERA_SIGHTING, requires manual attention, NOT auto-absent
    assert candidate_map[stu4.id].proposal_status is None
    assert candidate_map[stu4.id].evidence_state == EvidenceState.UNKNOWN
    assert candidate_map[stu4.id].requires_manual_attention is True
    assert candidate_map[stu4.id].uncertainty_reason == "NO_CAMERA_SIGHTING"


def test_conflict_detection_and_ambiguity_flagging(db_session, review_setup):
    session = review_setup["session"]
    stu1 = review_setup["stu1"]
    stu2 = review_setup["stu2"]

    batch = CaptureBatch(id=str(uuid.uuid4()), session_id=session.id)
    db_session.add(batch)
    db_session.flush()

    frame = Frame(
        id=str(uuid.uuid4()),
        batch_id=batch.id,
        frame_index=1,
        content_sha256="sha_conflict_frame",
        mime_type="image/jpeg",
        width=1920,
        height=1080,
        storage_path="conflict_frame.jpg",
    )
    db_session.add(frame)
    db_session.flush()

    # Two distinct faces in the SAME frame claiming stu1 -> CONFLICT
    ev1_a = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame.id,
        box_x1=10, box_y1=10, box_x2=100, box_y2=100,
        detection_score=0.95,
        candidate_student_id=stu1.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.68,
        score_margin=0.25,
        quality_score=0.90,
        model_artifact_hash="sface_v1_approved",
    )
    ev1_b = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame.id,
        box_x1=500, box_y1=10, box_x2=600, box_y2=100,
        detection_score=0.93,
        candidate_student_id=stu1.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.62,
        score_margin=0.20,
        quality_score=0.88,
        model_artifact_hash="sface_v1_approved",
    )

    # Face for stu2 with low margin (<0.10) -> AMBIGUOUS
    ev2 = FaceEvidence(
        id=str(uuid.uuid4()),
        frame_id=frame.id,
        box_x1=200, box_y1=10, box_x2=300, box_y2=100,
        detection_score=0.90,
        candidate_student_id=stu2.id,
        evidence_state=EvidenceState.CANDIDATE,
        similarity_score=0.55,
        score_margin=0.04,  # Narrow margin to 2nd candidate
        quality_score=0.85,
        model_artifact_hash="sface_v1_approved",
    )

    db_session.add_all([ev1_a, ev1_b, ev2])
    db_session.commit()

    proposal = ReviewService.generate_session_proposal(db_session, session.id)

    candidate_map = {c.student_id: c for c in proposal.candidates}

    # stu1: Multiple detections in single frame
    assert candidate_map[stu1.id].proposal_status is None
    assert candidate_map[stu1.id].evidence_state == EvidenceState.REVIEW
    assert candidate_map[stu1.id].requires_manual_attention is True
    assert candidate_map[stu1.id].uncertainty_reason == "SAME_FRAME_MULTIPLE_DETECTIONS_CONFLICT"

    # stu2: Narrow margin
    assert candidate_map[stu2.id].proposal_status is None
    assert candidate_map[stu2.id].evidence_state == EvidenceState.REVIEW
    assert candidate_map[stu2.id].requires_manual_attention is True
    assert candidate_map[stu2.id].uncertainty_reason == "LOW_MARGIN_AMBIGUOUS_CANDIDATE"


def test_adjudicate_session_proposal_audit_logging(db_session, review_setup):
    from app.api.v1.review import adjudicate_session_proposal, SessionAdjudicationRequest, CandidateAdjudicationItem
    from app.domain.models.audit import AuditEvent
    from app.domain.enums import AuditAction

    session = review_setup["session"]
    stu1 = review_setup["stu1"]
    faculty = review_setup["faculty"]
    faculty_user = review_setup["faculty_user"]

    req = SessionAdjudicationRequest(
        adjudications=[
            CandidateAdjudicationItem(
                student_id=stu1.id,
                status=AttendanceStatus.PRESENT_CONFIRMED,
                reason="VISUALLY_VERIFIED_BY_FACULTY",
            )
        ]
    )

    resp = adjudicate_session_proposal(
        session_id=session.id,
        request=req,
        db=db_session,
        faculty=faculty,
        current_user=faculty_user,
        correlation_id="corr-adj-123",
    )

    assert resp.data["adjudications_applied"] == 1
    assert resp.data["status"] == "ADJUDICATIONS_RECORDED"

    # Verify audit event was logged
    audit_row = db_session.query(AuditEvent).filter(
        AuditEvent.session_id == session.id,
        AuditEvent.action == AuditAction.PROPOSAL_REVIEWED,
    ).first()
    assert audit_row is not None
    assert audit_row.actor_id == faculty_user.id
    assert audit_row.correlation_id == "corr-adj-123"
