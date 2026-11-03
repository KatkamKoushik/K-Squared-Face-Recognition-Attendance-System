"""
FRS V7.1 K² — Data Governance, Biometric Privacy, Retention Purge & Cryptographic Receipt Verification Tests.
Verifies:
1. Server-side HMAC-SHA256 receipt signing and cryptographic tamper verification.
2. Ephemeral raw frame retention purging with physical file wiping and audit event emission.
3. Student biometric consent management and non-biometric manual roll-call routing.
4. Institutional governance compliance telemetry.
"""

from datetime import datetime, timezone, timedelta
import os
import tempfile
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import PermissionDeniedError, ResourceNotFoundError
from app.domain.enums import SessionState, AttendanceStatus, UnitStatus, AuditAction, UserRole
from app.domain.models.academic import User, Faculty
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot, SnapshotStudentItem
from app.domain.models.capture import CaptureBatch, Frame
from app.domain.models.student import Student, EnrollmentProfile
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent
from app.schemas.attendance import AttendanceCommitRequest, StudentUnitDecision
from app.schemas.governance import PurgeRequest, ConsentToggleRequest
from app.services.commit_service import CommitService
from app.services.governance_service import GovernanceService
from app.services.review_service import ReviewService


def test_cryptographic_receipt_hmac_signing_and_tamper_verification(db_session: Session, seed_data):
    """
    Verifies that attendance commits produce HMAC-SHA256 anchored receipts,
    and verify_session_receipt detects tampering with signatures or ledger row counts.
    """
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    students = seed_data["students"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add(u1)
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

    decisions = [
        StudentUnitDecision(student_id=students[0].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[1].id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
        StudentUnitDecision(student_id=students[2].id, unit_index=1, status=AttendanceStatus.ABSENT_CONFIRMED),
    ]

    commit_req = AttendanceCommitRequest(
        idempotency_key="idemp_hmac_receipt_001",
        conducted_unit_indices=[1],
        decisions=decisions,
    )

    receipt = CommitService.commit_session_attendance(
        db=db_session,
        session_id=session.id,
        user_id=fac_user.id,
        faculty_id=faculty.id,
        request=commit_req,
        correlation_id="corr-hmac-01",
    )

    assert receipt is not None
    assert receipt.receipt_hash is not None
    assert len(receipt.receipt_hash) == 64

    # 1. Genuine Verification Check -> Valid
    verify_result = CommitService.verify_session_receipt(
        db=db_session,
        session_id=session.id,
        user=fac_user,
    )
    assert verify_result.is_valid is True
    assert verify_result.signature_verified is True
    assert verify_result.ledger_records_matched is True
    assert verify_result.total_present_records == 2
    assert verify_result.total_absent_records == 1

    # 2. Tamper Test 1: Signature corruption detected
    original_hash = receipt.receipt_hash
    receipt.receipt_hash = "f" * 64
    db_session.flush()

    tampered_sig_result = CommitService.verify_session_receipt(
        db=db_session,
        session_id=session.id,
        user=fac_user,
    )
    assert tampered_sig_result.is_valid is False
    assert tampered_sig_result.signature_verified is False

    # Restore signature
    receipt.receipt_hash = original_hash
    db_session.flush()

    # 3. Tamper Test 2: Row discrepancy detected (tampering with underlying ledger)
    fake_rec = AttendanceRecord(
        session_id=session.id,
        unit_id=u1.id,
        student_id="extra_injected_student",
        status=AttendanceStatus.PRESENT_CONFIRMED,
        finalized_by_user_id=fac_user.id,
        reason_code="UNAUTHORIZED_INJECTION",
    )
    db_session.add(fake_rec)
    db_session.flush()

    tampered_row_result = CommitService.verify_session_receipt(
        db=db_session,
        session_id=session.id,
        user=fac_user,
    )
    assert tampered_row_result.is_valid is False
    assert tampered_row_result.ledger_records_matched is False


def test_ephemeral_raw_frame_retention_and_purging(db_session: Session, seed_data):
    """
    Verifies that raw photo frames on disk are physically unlinked and
    marked PURGED post-finalization, emitting DATA_PURGE_EXECUTED audit event.
    """
    faculty = seed_data["faculty"]
    fac_user = seed_data["faculty_user"]
    admin_user = seed_data["admin_user"]
    offering = seed_data["offering"]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.FINALIZED,
        planned_units=1,
        finalized_at=datetime.now(timezone.utc) - timedelta(days=10),  # 10 days ago (past 7-day retention)
    )
    db_session.add(session)
    db_session.flush()

    batch = CaptureBatch(session_id=session.id)
    db_session.add(batch)
    db_session.flush()

    # Create temporary dummy image file on disk
    temp_dir = tempfile.gettempdir()
    dummy_frame_path = os.path.join(temp_dir, f"test_purge_frame_{session.id}.jpg")
    with open(dummy_frame_path, "wb") as f:
        f.write(b"RAW_CLASSROOM_PIXEL_DATA_TO_BE_PURGED_2026")
    assert os.path.exists(dummy_frame_path)

    frame = Frame(
        batch_id=batch.id,
        frame_index=1,
        content_sha256="sha256_purge_test_frame_01",
        width=1920,
        height=1080,
        storage_path=dummy_frame_path,
        status="PROCESSED",
    )
    db_session.add(frame)
    db_session.flush()

    # 1. Non-admin cannot execute purge -> PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        GovernanceService.purge_raw_frames(
            db=db_session,
            request=PurgeRequest(retention_days=7),
            user=fac_user,
            correlation_id="corr-purge-err",
        )

    # 2. Admin executes purge -> physical file unlinked, frame marked PURGED
    purge_resp = GovernanceService.purge_raw_frames(
        db=db_session,
        request=PurgeRequest(retention_days=7),
        user=admin_user,
        correlation_id="corr-purge-ok",
    )

    assert purge_resp.purged_frames_count >= 1
    assert purge_resp.freed_bytes > 0
    assert not os.path.exists(dummy_frame_path)  # File removed from disk

    db_session.refresh(frame)
    assert frame.status == "PURGED"
    assert frame.storage_path.startswith("[PURGED_AT_")

    # 3. Verify append-only AuditEvent logged
    audit = db_session.get(AuditEvent, purge_resp.audit_event_id)
    assert audit is not None
    assert audit.action == AuditAction.DATA_PURGE_EXECUTED
    assert audit.actor_id == admin_user.id
    assert audit.after_state["freed_bytes"] == purge_resp.freed_bytes


def test_student_biometric_consent_and_non_biometric_fallback(db_session: Session, seed_data):
    """
    Verifies that revoking biometric consent deactivates enrollment profile,
    and ReviewService routes the student to non-biometric manual roll-call.
    """
    faculty = seed_data["faculty"]
    students = seed_data["students"]
    admin_user = seed_data["admin_user"]
    offering = seed_data["offering"]

    target_student = students[0]

    # Create active biometric enrollment profile for student
    profile = EnrollmentProfile(
        student_id=target_student.id,
        model_artifact_id="sface_onnx_hash",
        embedding_namespace="sface_128d_v1",
        embedding_dimension=128,
        vector_data=[0.1] * 128,
        profile_version=1,
        is_active=True,
    )
    db_session.add(profile)
    db_session.flush()

    # Create session with target student
    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=1,
    )
    db_session.add(session)
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=1)
    db_session.add(snapshot)
    db_session.flush()

    item = SnapshotStudentItem(
        snapshot_id=snapshot.id,
        student_id=target_student.id,
        roll_number=target_student.roll_number,
        full_name=target_student.full_name,
        cohort_id=target_student.cohort_id,
    )
    db_session.add(item)
    db_session.flush()

    # Action 1: Deactivate biometric consent (student opts for non-biometric alternative)
    consent_resp = GovernanceService.toggle_student_biometric_consent(
        db=db_session,
        request=ConsentToggleRequest(
            student_id=target_student.id,
            consent_active=False,
            reason="Student requested alternative non-biometric roll-call procedure.",
        ),
        user=admin_user,
        correlation_id="corr-consent-01",
    )
    assert consent_resp.biometric_consent_active is False
    assert consent_resp.alternative_roll_call_required is True

    db_session.refresh(profile)
    assert profile.is_active is False

    # Action 2: Review proposals routes student to explicit non-biometric alternative
    proposal_resp = ReviewService.generate_session_proposal(db=db_session, session_id=session.id)
    cand = proposal_resp.candidates[0]
    assert cand.student_id == target_student.id
    assert cand.proposal_status is None
    assert cand.evidence_state.value == "UNKNOWN"
    assert cand.requires_manual_attention is True
    assert "NON_BIOMETRIC_ALTERNATIVE_REQUIRED" in cand.uncertainty_reason

    # Action 3: Governance summary reflects consent metrics
    summary = GovernanceService.get_governance_summary(db=db_session)
    assert summary.total_students >= 1
    assert summary.students_withheld_consent >= 1

