"""
K² FRS — Transactional Outbox Event Broadcaster Test Suite.
Verifies outbox table persistence, cross-process replayability, and durable SSE synchronization.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from app.domain.models.outbox import OutboxEvent
from app.schemas.events import EventMessage, RealtimeEventType
from app.services.event_broadcaster import EventBroadcaster


def test_outbox_publish_sync_writes_to_database(db_session):
    broadcaster = EventBroadcaster(buffer_size=10)
    event = EventMessage(
        event_type=RealtimeEventType.SESSION_STATE_CHANGED,
        channel="session:test-session-outbox",
        payload={"state": "PROPOSAL_READY", "student_count": 35},
    )

    broadcaster.publish_sync(event, db=db_session)
    db_session.commit()

    saved_row = db_session.query(OutboxEvent).filter(OutboxEvent.id == event.event_id).first()
    assert saved_row is not None
    assert saved_row.event_type == RealtimeEventType.SESSION_STATE_CHANGED.value
    assert saved_row.channel == "session:test-session-outbox"
    assert saved_row.payload["state"] == "PROPOSAL_READY"
    assert saved_row.payload["student_count"] == 35
    # Transactional outbox invariant: initially recorded as unpublished pending dispatch
    assert saved_row.is_published is False
    assert saved_row.published_at is None

    # Relay dispatcher processes pending outbox events
    dispatched = broadcaster.dispatch_pending_outbox_events(db_session)
    assert dispatched >= 1
    db_session.commit()

    db_session.refresh(saved_row)
    assert saved_row.is_published is True
    assert saved_row.published_at is not None


@pytest.mark.asyncio
async def test_outbox_replay_across_cleared_memory_buffer(db_session):
    broadcaster = EventBroadcaster(buffer_size=10)

    # 1. Publish two events to the database outbox
    event1 = EventMessage(
        event_type=RealtimeEventType.SESSION_STATE_CHANGED,
        channel="session:test-session-outbox-2",
        payload={"step": 1},
    )
    event2 = EventMessage(
        event_type=RealtimeEventType.PROPOSAL_READY,
        channel="session:test-session-outbox-2",
        payload={"step": 2, "verified_faces": 38},
    )

    await broadcaster.publish(event1, db=db_session)
    await broadcaster.publish(event2, db=db_session)
    db_session.commit()

    # 2. Simulate complete in-memory eviction / server restart
    broadcaster._history.clear()
    assert len(broadcaster._history) == 0

    # 3. Subscribe with last_event_id=event1.event_id and db=db_session
    recovered_events = []
    async def collect_one():
        async for ev in broadcaster.subscribe(
            allowed_channels={"session:test-session-outbox-2"},
            last_event_id=event1.event_id,
            db=db_session,
        ):
            recovered_events.append(ev)
            break

    await asyncio.wait_for(collect_one(), timeout=2.0)
    assert len(recovered_events) == 1
    assert recovered_events[0].event_id == event2.event_id
    assert recovered_events[0].event_type == RealtimeEventType.PROPOSAL_READY
    assert recovered_events[0].payload["verified_faces"] == 38


def test_commit_service_atomically_persists_outbox_event(db_session, seed_data):
    """Verify that CommitService.commit_session_attendance persists RECEIPT_ISSUED outbox event inside attendance transaction."""
    from app.services.commit_service import CommitService
    from app.domain.enums import SessionState
    from app.domain.models.session import AttendanceSession, RosterSnapshot, SnapshotStudentItem
    from app.domain.enums import AttendanceStatus
    from app.schemas.attendance import AttendanceCommitRequest, StudentUnitDecision

    faculty = seed_data["faculty"]
    faculty_user = seed_data["faculty_user"]
    offering = seed_data["offering"]
    student = seed_data["students"][0]

    session = AttendanceSession(
        offering_id=offering.id,
        faculty_id=faculty.id,
        state=SessionState.IN_REVIEW,
        planned_units=2,
    )
    db_session.add(session)
    db_session.flush()

    from app.domain.models.session import AttendanceUnit
    from app.domain.enums import UnitStatus
    u1 = AttendanceUnit(session_id=session.id, unit_index=1, is_conducted=True, status=UnitStatus.PENDING)
    u2 = AttendanceUnit(session_id=session.id, unit_index=2, is_conducted=True, status=UnitStatus.PENDING)
    db_session.add_all([u1, u2])
    db_session.flush()

    snapshot = RosterSnapshot(session_id=session.id, snapshot_version=1, total_eligible_students=1)
    db_session.add(snapshot)
    db_session.flush()

    item = SnapshotStudentItem(
        snapshot_id=snapshot.id,
        student_id=student.id,
        roll_number=student.roll_number,
        full_name=student.full_name,
        cohort_id=student.cohort_id,
    )
    db_session.add(item)
    db_session.commit()

    commit_req = AttendanceCommitRequest(
        idempotency_key="idemp-outbox-commit-test-01",
        conducted_unit_indices=[1, 2],
        decisions=[
            StudentUnitDecision(student_id=student.id, unit_index=1, status=AttendanceStatus.PRESENT_CONFIRMED),
            StudentUnitDecision(student_id=student.id, unit_index=2, status=AttendanceStatus.PRESENT_CONFIRMED),
        ],
    )

    receipt = CommitService.commit_session_attendance(
        db=db_session,
        session_id=session.id,
        user_id=faculty_user.id,
        faculty_id=faculty.id,
        request=commit_req,
        correlation_id="corr-outbox-test-01",
    )
    db_session.commit()

    assert receipt is not None
    # Check that outbox table has the RECEIPT_ISSUED event committed atomically
    outbox_event = (
        db_session.query(OutboxEvent)
        .filter(
            OutboxEvent.channel == f"session:{session.id}",
            OutboxEvent.event_type == RealtimeEventType.RECEIPT_ISSUED.value,
        )
        .first()
    )
    assert outbox_event is not None
    assert outbox_event.payload["session_id"] == session.id
    assert outbox_event.payload["receipt_hash"] == receipt.receipt_hash
