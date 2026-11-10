"""
FRS V7.1 K² — Strict Inference, Fail-Closed PAD & Attendance Decision Invariant Tests.
Verifies zero synthetic identities, fail-closed liveness security gates,
and atomic attendance decisions with complete cartesian product enforcement.
"""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.domain.enums import AttendanceStatus
from app.services.commit_service import CommitService
from app.schemas.attendance import AttendanceCommitRequest, StudentUnitDecision
from app.worker.adapters.detector_adapter import DetectorAdapter
from app.worker.adapters.recognizer_adapter import RecognizerAdapter
from app.worker.adapters.pad_adapter import PadAdapter


# ==============================================================================
# 1. PAD FAIL-CLOSED TESTS
# ==============================================================================

def test_pad_missing_face_crop_fails_closed():
    """PAD gate must fail closed and return ERROR when face crop is None."""
    pad = PadAdapter()
    result = pad.verify_liveness(None, mandatory=True)
    assert result.is_live is False
    assert result.status == "ERROR"
    assert "PAD_MISSING_FACE_CROP" in result.reason_code


def test_pad_invalid_dimensions_fails_closed():
    """PAD gate must fail closed when image dimensions are 0x0."""
    pad = PadAdapter()
    empty_crop = Image.new("RGB", (0, 0))
    result = pad.verify_liveness(empty_crop, mandatory=True)
    assert result.is_live is False
    assert result.status == "ERROR"


def test_pad_flat_uniform_surface_returns_uncertain():
    """Flat display or printout simulation (zero texture variance) must return UNCERTAIN, never PASS."""
    pad = PadAdapter()
    flat_crop = Image.new("RGB", (112, 112), color=(180, 180, 180))
    result = pad.verify_liveness(flat_crop, mandatory=True)
    assert result.is_live is False
    assert result.status == "UNCERTAIN"
    assert "PAD_LOW_TEXTURE" in result.reason_code


def test_pad_natural_skin_texture_passes_when_above_threshold():
    """Natural high-frequency skin gradient passes PAD gate."""
    pad = PadAdapter()
    arr = np.zeros((112, 112, 3), dtype=np.uint8)
    arr[::2, ::2] = 255
    arr[1::2, 1::2] = 120
    textured_crop = Image.fromarray(arr)
    result = pad.verify_liveness(textured_crop, mandatory=True, threshold=0.75)
    assert result.is_live is True
    assert result.status == "PASS"


def test_pad_skipped_when_not_mandatory_still_returns_is_live_false():
    """Supervised bypass must clearly report SKIPPED and is_live=False."""
    pad = PadAdapter()
    crop = Image.new("RGB", (112, 112), color=(200, 200, 200))
    result = pad.verify_liveness(crop, mandatory=False)
    assert result.is_live is False
    assert result.status == "SKIPPED"


# ==============================================================================
# 2. MODEL INTEGRITY & STRICT ERROR TRANSPARENCY TESTS
# ==============================================================================

def test_detector_missing_file_raises_filenotfound():
    """Missing YuNet model weights must raise FileNotFoundError in strict mode."""
    non_existent = Path("/tmp/non_existent_weights_12345.onnx")
    with pytest.raises(FileNotFoundError) as exc_info:
        DetectorAdapter(model_path=non_existent, strict_mode=True)
    assert "not found" in str(exc_info.value).lower()


def test_detector_hash_mismatch_raises_valueerror(tmp_path):
    """Corrupted ONNX file with wrong hash must raise ValueError in strict mode."""
    corrupt_file = tmp_path / "corrupt_detector.onnx"
    corrupt_file.write_bytes(b"CORRUPTED_ONNX_MODEL_BYTES_WITH_WRONG_SHA256")
    with pytest.raises(ValueError) as exc_info:
        DetectorAdapter(model_path=corrupt_file, strict_mode=True)
    assert "hash mismatch" in str(exc_info.value).lower()


def test_recognizer_missing_file_raises_filenotfound():
    """Missing SFace model weights must raise FileNotFoundError in strict mode."""
    non_existent = Path("/tmp/non_existent_sface_12345.onnx")
    with pytest.raises(FileNotFoundError) as exc_info:
        RecognizerAdapter(model_path=non_existent, strict_mode=True)
    assert "not found" in str(exc_info.value).lower()


def test_recognizer_empty_gallery_returns_empty_reason():
    """Searching an empty gallery must cleanly return GALLERY_EMPTY_NO_ENROLLED_PROFILES."""
    recognizer = RecognizerAdapter()
    query = [1.0] + [0.0] * 127
    candidate = recognizer.search_exact_roster(
        query_vector=query,
        enrolled_profiles={},
    )
    assert candidate.is_matched is False
    assert candidate.reason_code == "GALLERY_EMPTY_NO_ENROLLED_PROFILES"


# ==============================================================================
# 3. ATTENDANCE DECISION INVARIANT TESTS
# ==============================================================================

def test_commit_incomplete_decision_matrix_fails(db_session: Session, seed_data):
    """
    FR-08: Incomplete Decision Matrix Completeness.
    Submitting decisions for only a subset of eligible roster students must raise ValueError,
    preventing any silent absence defaults.
    """
    from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot, SnapshotStudentItem
    from app.domain.models.academic import User, Faculty, SubjectOffering
    from app.domain.enums import SessionState, UnitStatus

    fac = db_session.query(Faculty).first()
    offering = db_session.query(SubjectOffering).first()

    # 1. Create session with 2 eligible students in frozen roster
    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=fac.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    u1 = AttendanceUnit(session_id=session.id, unit_index=1, status=UnitStatus.PENDING)
    u2 = AttendanceUnit(session_id=session.id, unit_index=2, status=UnitStatus.PENDING)
    db_session.add_all([u1, u2])

    snapshot = RosterSnapshot(session_id=session.id, total_eligible_students=2)
    db_session.add(snapshot)
    db_session.flush()

    s1 = SnapshotStudentItem(snapshot_id=snapshot.id, student_id="STU-001", roll_number="22016A0501", full_name="Student 1", cohort_id=offering.primary_cohort_id)
    s2 = SnapshotStudentItem(snapshot_id=snapshot.id, student_id="STU-002", roll_number="22016A0502", full_name="Student 2", cohort_id=offering.primary_cohort_id)
    db_session.add_all([s1, s2])
    db_session.commit()

    # 2. Faculty only adjudicates Student 1, forgetting Student 2
    incomplete_request = AttendanceCommitRequest(
        idempotency_key="TEST-IDEMP-INCOMPLETE-01",
        conducted_unit_indices=[1, 2],
        decisions=[
            StudentUnitDecision(student_id="STU-001", unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
            StudentUnitDecision(student_id="STU-001", unit_index=2, status=AttendanceStatus.PRESENT_CONFIRMED),
        ],
    )

    with pytest.raises(ValueError) as exc_info:
        CommitService.commit_session_attendance(
            db=db_session,
            session_id=session.id,
            user_id=fac.user_id,
            faculty_id=fac.id,
            request=incomplete_request,
            correlation_id="test-corr",
        )
    assert "Incomplete attendance decision matrix" in str(exc_info.value)
    assert "Missing decisions for 2 student-unit combinations" in str(exc_info.value)
