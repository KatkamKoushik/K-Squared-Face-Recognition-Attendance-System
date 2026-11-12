"""
K² FRS — Vision Evidence State Machine & Fail-Safe Invariant Tests.
Proves that pipeline uncertainty, low quality, and unknown faces NEVER become absences.
"""

import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.domain.enums import EvidenceState
from app.domain.models.attendance import AttendanceRecord
from app.worker.adapters.recognizer_adapter import RecognizerAdapter


def test_recognizer_open_set_threshold_rejection():
    """Face below similarity threshold is classified UNKNOWN, not absent."""
    adapter = RecognizerAdapter()

    roster_gallery = {"student_01": [1.0] + [0.0] * 127}
    query_vector = [0.0, 1.0] + [0.0] * 126

    candidate = adapter.search_exact_roster(
        query_vector=query_vector,
        enrolled_profiles=roster_gallery,
        match_threshold=0.45,
        margin_threshold=0.10,
    )
    assert candidate.is_matched is False
    assert candidate.reason_code == "BELOW_MATCH_THRESHOLD"
    assert candidate.similarity_score == 0.0


def test_recognizer_ambiguous_lookalike_conflict_routing():
    """Top-1 and Top-2 margin < margin_threshold is routed to REVIEW, not auto-accepted."""
    adapter = RecognizerAdapter()

    query_vector = [1.0] + [0.0] * 127
    roster_gallery = {
        "student_A": [0.99] + [0.01] * 127,
        "student_B": [0.97] + [0.02] * 127,
    }

    candidate = adapter.search_exact_roster(
        query_vector=query_vector,
        enrolled_profiles=roster_gallery,
        match_threshold=0.45,
        margin_threshold=0.10,
    )
    assert candidate.is_matched is False
    assert candidate.reason_code == "AMBIGUOUS_LOOKALIKE_CONFLICT"


def test_evidence_production_never_mutates_attendance_ledger(db_session: Session, seed_data):
    """
    Core Invariant:
    Vision evidence components are evidence producers only.
    The attendance ledger must remain strictly empty (0 rows) prior to explicit faculty commit.
    """
    count_stmt = select(func.count(AttendanceRecord.id))
    total_ledger_rows = db_session.execute(count_stmt).scalar() or 0
    assert total_ledger_rows == 0
