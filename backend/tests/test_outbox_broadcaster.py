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
    assert saved_row.is_published is True


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
