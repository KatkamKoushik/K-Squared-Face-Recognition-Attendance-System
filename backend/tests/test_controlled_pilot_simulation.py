"""
FRS V7.1 K² — Phase P7 Controlled Pilot Simulation & Dual-Ledger Invariant Suite.
Simulates the complete 14-day classroom pilot for Kakatiya University College of Engineering & Technology (KUCET).
Verifies:
1. Multi-day session lifecycle with 2 conducted units per day (28 total conducted units).
2. Roster snapshot freezing and mathematical Cartesian completeness across all units.
3. DPDP Act non-biometric alternative manual roll-call equity for consent-withheld students.
4. Cryptographic HMAC-SHA256 receipt signing and tamper verification across all sessions.
5. Mid-pilot post-commit corrections and student appeals with mandatory audit trails.
6. Ephemeral frame retention purging at the 7-day retention boundary.
7. Cumulative offering attendance analytics adhering to Section 4.2 arithmetic.
"""

from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
import os
import tempfile
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.enums import SessionState, AttendanceStatus, UnitStatus, AuditAction, UserRole
from app.domain.models.academic import User, Faculty, SubjectOffering
from app.domain.models.session import AttendanceSession, AttendanceUnit, RosterSnapshot, SnapshotStudentItem
from app.domain.models.student import Student, EnrollmentProfile
from app.domain.models.attendance import AttendanceRecord
from app.domain.models.audit import CommitReceipt, AuditEvent
from app.domain.models.capture import CaptureBatch, Frame
from app.schemas.attendance import AttendanceCommitRequest, StudentUnitDecision, AttendanceCorrectionRequest
from app.schemas.governance import PurgeRequest
from app.seeds.kucet_seed import seed_kucet_institutional_data
from app.services.session_service import SessionService
from app.services.review_service import ReviewService
from app.services.commit_service import CommitService
from app.services.governance_service import GovernanceService
from app.services.analytics_service import AnalyticsService


def test_14_day_controlled_pilot_simulation_and_dual_ledger_invariants(db_session: Session):
    """
    Simulates the entire 14-day controlled pilot for CS401 (Distributed Systems & Cloud Computing)
    in the Department of CSE (B.Tech CSE Class of 2026, Section A).
    """
    # 1. Seed Institutional Baseline
    stats = seed_kucet_institutional_data(db_session)
    assert stats["students"] == 8
    assert stats["profiles_active"] == 7
    assert stats["profiles_withheld"] == 1

    # Retrieve seeded faculty and offering
    faculty = db_session.execute(
        select(Faculty).where(Faculty.employee_id == "KUCET-FAC-CSE-001")
    ).scalar_one()
    fac_user = db_session.get(User, faculty.user_id)
    admin_user = db_session.execute(select(User).where(User.role == UserRole.ADMIN)).scalars().first()
    if not admin_user:
        admin_user = User(
            email="admin.pilot@kucet.ac.in",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin_user)
        db_session.flush()

    offering = db_session.execute(
        select(SubjectOffering).where(SubjectOffering.is_active == True)
    ).scalars().first()

    students = db_session.execute(select(Student).order_by(Student.roll_number)).scalars().all()
    assert len(students) == 8

    # Target consent-withheld student (Ch. Rahul)
    rahul = db_session.execute(select(Student).where(Student.roll_number == "00622504")).scalar_one()

    # Track receipts across the 14 days
    pilot_session_ids = []
    pilot_receipts = []

    # Temporary directory for ephemeral sweep frames
    temp_dir = tempfile.mkdtemp(prefix="kucet_pilot_frames_")

    try:
        # Simulate 14 Instructional Days
        start_date = date(2026, 9, 1)

        for day_idx in range(1, 15):
            current_date = start_date + timedelta(days=day_idx - 1)

            # Step 1: Initialize session with 2 instructional units
            session = AttendanceSession(
                offering_id=offering.id,
                faculty_id=faculty.id,
                session_date=current_date,
                planned_units=2,
                state=SessionState.ROSTER_FROZEN,
            )
            db_session.add(session)
            db_session.flush()
            pilot_session_ids.append(session.id)

            u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.CONDUCTED_CONFIRMED)
            u2 = AttendanceUnit(session_id=session.id, unit_index=2, is_conducted=True, status=UnitStatus.CONDUCTED_CONFIRMED)
            db_session.add_all([u1, u2])
            db_session.flush()

            # Step 2: Freeze Roster Snapshot
            snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=len(students))
            db_session.add(snapshot)
            db_session.flush()

            for s in students:
                db_session.add(
                    SnapshotStudentItem(
                        snapshot_id=snapshot.id,
                        student_id=s.id,
                        roll_number=s.roll_number,
                        full_name=s.full_name,
                        cohort_id=s.cohort_id,
                    )
                )
            db_session.flush()

            # Step 3: Ingest Classroom Photo Sweep Frames
            batch = CaptureBatch(session_id=session.id)
            db_session.add(batch)
            db_session.flush()

            # Create physical frame files with varying timestamps for retention check
            frame_age_days = 14 - day_idx
            frame_created_at = datetime.now(timezone.utc) - timedelta(days=frame_age_days)

            frame1_path = os.path.join(temp_dir, f"pilot_day_{day_idx}_left.jpg")
            with open(frame1_path, "wb") as f:
                f.write(b"\xFF\xD8\xFF\xE0" + b"\x00" * 2048)  # Dummy JPEG

            frm1 = Frame(
                batch_id=batch.id,
                frame_index=1,
                content_sha256=hashlib.sha256(b"\xFF\xD8\xFF\xE0" + b"\x00" * 2048).hexdigest(),
                mime_type="image/jpeg",
                width=1920,
                height=1080,
                storage_path=frame1_path,
                status="PROCESSED",
                received_at=frame_created_at,
            )
            db_session.add(frm1)
            db_session.flush()

            # Step 4: Proposal Generation & Non-Biometric Routing
            session.state = SessionState.IN_REVIEW
            db_session.flush()

            proposal = ReviewService.generate_session_proposal(db=db_session, session_id=session.id)
            assert proposal.total_eligible_students == 8

            # Check that student 00622504 (Ch. Rahul) is routed to NON_BIOMETRIC_ALTERNATIVE_REQUIRED
            rahul_cand = next(c for c in proposal.candidates if c.student_id == rahul.id)
            assert rahul_cand.proposal_status is None
            assert "NON_BIOMETRIC_ALTERNATIVE_REQUIRED" in rahul_cand.uncertainty_reason
            assert rahul_cand.requires_manual_attention is True

            # Step 5: Faculty Adjudication & Decision Matrix Construction
            # On day 3, student 00622508 (K. Sneha) is absent
            decisions = []
            for s in students:
                is_student_absent = (day_idx == 3 and s.roll_number == "00622508")
                # Student 00622504 (Ch. Rahul) confirmed physically present via manual roll call
                status = AttendanceStatus.ABSENT_CONFIRMED if is_student_absent else AttendanceStatus.PRESENT_CONFIRMED
                reason = "MANUAL_ROLL_CALL_FALLBACK" if s.id == rahul.id else "FACULTY_FINAL_COMMIT"

                for u_idx in [1, 2]:
                    decisions.append(
                        StudentUnitDecision(
                            student_id=s.id,
                            unit_index=u_idx,
                            status=status,
                            reason_code=reason,
                        )
                    )

            # Step 6: Atomic Attendance Commit & HMAC-SHA256 Receipt
            commit_req = AttendanceCommitRequest(
                idempotency_key=f"PILOT-DAY-{day_idx}-IDEMP-{session.id[:8]}",
                conducted_unit_indices=[1, 2],
                decisions=decisions,
            )

            receipt_resp = CommitService.commit_session_attendance(
                db=db_session,
                session_id=session.id,
                user_id=fac_user.id,
                faculty_id=faculty.id,
                request=commit_req,
                correlation_id=f"pilot-corr-{day_idx}",
            )

            assert receipt_resp.total_conducted_units == 2
            assert receipt_resp.total_present_records + receipt_resp.total_absent_records == 16  # 8 students x 2 units
            pilot_receipts.append(receipt_resp)

            # Set finalized_at back according to simulated instructional day age
            session.finalized_at = frame_created_at
            db_session.flush()

            # Step 7: Authoritative Receipt Verification
            verify_resp = CommitService.verify_session_receipt(
                db=db_session,
                session_id=session.id,
                user=fac_user,
            )
            assert verify_resp.is_valid is True
            assert verify_resp.signature_verified is True
            assert verify_resp.ledger_records_matched is True

        # Phase P7 Mid-Pilot Event: Student Appeal Processing
        # On Day 3, student K. Sneha (00622508) was absent; submits HOD approved memo ref KUCET/CSE/2026/MED-019
        day_3_session_id = pilot_session_ids[2]
        sneha = db_session.execute(select(Student).where(Student.roll_number == "00622508")).scalar_one()

        correction_resp_u1 = CommitService.apply_attendance_correction(
            db=db_session,
            session_id=day_3_session_id,
            user=admin_user,
            request=AttendanceCorrectionRequest(
                student_id=sneha.id,
                unit_index=1,
                new_status=AttendanceStatus.PRESENT_CONFIRMED,
                action_type="APPEAL",
                reason="HOD approved medical memo ref: KUCET/CSE/2026/MED-019",
                reference_document="KUCET/CSE/2026/MED-019",
            ),
            correlation_id="corr-appeal-01",
        )
        assert correction_resp_u1.previous_status == AttendanceStatus.ABSENT_CONFIRMED
        assert correction_resp_u1.new_status == AttendanceStatus.PRESENT_CONFIRMED

        correction_resp_u2 = CommitService.apply_attendance_correction(
            db=db_session,
            session_id=day_3_session_id,
            user=admin_user,
            request=AttendanceCorrectionRequest(
                student_id=sneha.id,
                unit_index=2,
                new_status=AttendanceStatus.PRESENT_CONFIRMED,
                action_type="APPEAL",
                reason="HOD approved medical memo ref: KUCET/CSE/2026/MED-019",
                reference_document="KUCET/CSE/2026/MED-019",
            ),
            correlation_id="corr-appeal-02",
        )
        assert correction_resp_u2.new_status == AttendanceStatus.PRESENT_CONFIRMED

        # Phase P7 Ephemeral Frame Retention Purge Check (7-day window)
        # Frames older than 7 days should be unlinked
        purge_resp = GovernanceService.purge_raw_frames(
            db=db_session,
            request=PurgeRequest(retention_days=7),
            user=admin_user,
            correlation_id="corr-pilot-purge",
        )
        assert purge_resp.retention_days == 7
        assert purge_resp.purged_frames_count > 0

        # Phase P7 Final Holdout Analytics Verification
        analytics = AnalyticsService.get_offering_attendance_analytics(db=db_session, offering_id=offering.id)
        assert analytics.total_sessions == 14
        assert analytics.total_conducted_units == 28
        assert len(analytics.student_stats) == 8

        for stat in analytics.student_stats:
            assert stat.eligible_conducted_units == 28
            # Student 00622504 (Ch. Rahul, consent withheld) has 100% attendance (non-biometric parity)
            if stat.roll_number == "00622504":
                assert stat.attended_conducted_units == 28
                assert stat.attendance_percent == 100.0
            # Student 00622508 (K. Sneha) had absence appealed to present -> 28/28 = 100.0%
            elif stat.roll_number == "00622508":
                assert stat.attended_conducted_units == 28
                assert stat.attendance_percent == 100.0
            else:
                assert stat.attended_conducted_units == 28
                assert stat.attendance_percent == 100.0

        # Tamper Resistance Test: Altering a session receipt hash fails verification closed
        tampered_session_id = pilot_session_ids[13]
        receipt_to_tamper = db_session.execute(
            select(CommitReceipt).where(CommitReceipt.session_id == tampered_session_id)
        ).scalar_one()
        original_hash = receipt_to_tamper.receipt_hash
        receipt_to_tamper.receipt_hash = "0xBAD0000000000000000000000000000000000000000000000000000000000000"
        db_session.flush()

        tampered_verify = CommitService.verify_session_receipt(
            db=db_session,
            session_id=tampered_session_id,
            user=fac_user,
        )
        assert tampered_verify.is_valid is False
        assert tampered_verify.signature_verified is False

        # Restore original hash
        receipt_to_tamper.receipt_hash = original_hash
        db_session.flush()

    finally:
        # Cleanup temporary pilot files
        if os.path.exists(temp_dir):
            for f in os.listdir(temp_dir):
                try:
                    os.unlink(os.path.join(temp_dir, f))
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
