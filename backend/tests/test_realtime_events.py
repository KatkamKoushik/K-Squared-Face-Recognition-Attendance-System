"""
K² FRS — Real-Time Event Broadcaster & SSE Test Suite.
Verifies channel authorization, event serialization, replay buffers, and live streams.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import create_application
from app.core.database import get_db
from app.domain.enums import UserRole
from app.domain.models.academic import Department, Cohort, Subject, SubjectOffering, User
from app.schemas.events import EventMessage, RealtimeEventType
from app.services.event_broadcaster import EventBroadcaster, validate_channel_subscription


@pytest.fixture
def mock_broadcaster():
    return EventBroadcaster(buffer_size=10)


@pytest.fixture
def app(db_session):
    application = create_application()
    application.dependency_overrides[get_db] = lambda: db_session
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


def test_event_message_sse_formatting():
    msg = EventMessage(
        event_type=RealtimeEventType.SESSION_STATE_CHANGED,
        channel="session:sess-123",
        payload={"state": "ROSTER_FROZEN", "session_id": "sess-123"},
    )
    sse_text = msg.to_sse()
    assert f"id: {msg.event_id}\n" in sse_text
    assert f"event: {RealtimeEventType.SESSION_STATE_CHANGED.value}\n" in sse_text
    assert "data: {" in sse_text
    assert '"channel": "session:sess-123"' in sse_text
    assert sse_text.endswith("\n\n")


@pytest.mark.asyncio
async def test_broadcaster_publish_and_subscribe(mock_broadcaster):
    msg1 = EventMessage(
        event_type=RealtimeEventType.SESSION_STATE_CHANGED,
        channel="department:dept-cse",
        payload={"count": 1},
    )
    msg2 = EventMessage(
        event_type=RealtimeEventType.ENROLLMENT_SUBMITTED,
        channel="global:admin",
        payload={"count": 2},
    )

    async def consumer():
        events = []
        async for ev in mock_broadcaster.subscribe(allowed_channels={"department:dept-cse"}):
            events.append(ev)
            if len(events) == 1:
                break
        return events

    consumer_task = asyncio.create_task(consumer())
    await asyncio.sleep(0.01)

    await mock_broadcaster.publish(msg2)  # Should not be received by consumer (wrong channel)
    await mock_broadcaster.publish(msg1)  # Should be received

    received = await asyncio.wait_for(consumer_task, timeout=1.0)
    assert len(received) == 1
    assert received[0].channel == "department:dept-cse"
    assert received[0].payload["count"] == 1


@pytest.mark.asyncio
async def test_broadcaster_reconnection_replay(mock_broadcaster):
    # Publish 3 events
    msg1 = EventMessage(event_type=RealtimeEventType.SESSION_STATE_CHANGED, channel="dept:1", payload={"id": 1})
    msg2 = EventMessage(event_type=RealtimeEventType.SESSION_STATE_CHANGED, channel="dept:1", payload={"id": 2})
    msg3 = EventMessage(event_type=RealtimeEventType.SESSION_STATE_CHANGED, channel="dept:1", payload={"id": 3})

    await mock_broadcaster.publish(msg1)
    await mock_broadcaster.publish(msg2)
    await mock_broadcaster.publish(msg3)

    # Reconnect asking for events after msg1
    events = []
    async for ev in mock_broadcaster.subscribe(allowed_channels={"dept:1"}, last_event_id=msg1.event_id):
        events.append(ev)
        if len(events) == 2:
            break

    assert len(events) == 2
    assert events[0].event_id == msg2.event_id
    assert events[1].event_id == msg3.event_id


def test_validate_channel_subscription_permissions(db_session):
    dept_cse = Department(name="Computer Science & Engineering", code="CSE-RT")
    dept_ece = Department(name="Electronics & Communication", code="ECE-RT")
    db_session.add_all([dept_cse, dept_ece])
    db_session.flush()

    super_admin = User(
        email="superadmin@kucet.ac.in",
        role=UserRole.SUPER_ADMIN,
        hashed_password="pw",
        is_active=True,
    )
    cse_admin = User(
        email="csetest@kucet.ac.in",
        role=UserRole.ADMIN,
        department_id=dept_cse.id,
        hashed_password="pw",
        is_active=True,
    )
    student_user = User(
        email="student@kucet.ac.in",
        role=UserRole.STUDENT,
        department_id=dept_cse.id,
        hashed_password="pw",
        is_active=True,
    )
    db_session.add_all([super_admin, cse_admin, student_user])
    db_session.commit()

    # 1. Super admin can access all channels
    assert validate_channel_subscription(super_admin, "global:admin", db_session) is True
    assert validate_channel_subscription(super_admin, f"department:{dept_cse.id}", db_session) is True
    assert validate_channel_subscription(super_admin, f"user:{student_user.id}", db_session) is True

    # 2. CSE Admin can access cse department channel, but not ece or global:admin
    assert validate_channel_subscription(cse_admin, f"department:{dept_cse.id}", db_session) is True
    assert validate_channel_subscription(cse_admin, f"department:{dept_ece.id}", db_session) is False
    assert validate_channel_subscription(cse_admin, "global:admin", db_session) is False

    # 3. Student can only access their own user channel
    assert validate_channel_subscription(student_user, f"user:{student_user.id}", db_session) is True
    assert validate_channel_subscription(student_user, f"user:{cse_admin.id}", db_session) is False
    assert validate_channel_subscription(student_user, f"department:{dept_cse.id}", db_session) is False
    assert validate_channel_subscription(student_user, "global:admin", db_session) is False


def test_sse_endpoint_unauthorized_channel(client, seed_data, db_session):
    student_user = User(
        email="sse_student@kucet.ac.in",
        role=UserRole.STUDENT,
        department_id=seed_data["department"].id,
        hashed_password="pw",
        is_active=True,
    )
    db_session.add(student_user)
    db_session.commit()

    from app.core.security import create_access_token
    token = create_access_token(
        subject=student_user.id,
        role=student_user.role.value,
        additional_claims={"email": student_user.email, "department_id": seed_data["department"].id},
    )

    # Student trying to subscribe to global:admin channel should fail with 403 Forbidden
    response = client.get(
        "/api/v1/events/stream?channels=global:admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["error"]["message"]


def test_sse_endpoint_authorized_channel(client, seed_data, db_session):
    student_user = User(
        email="sse_student2@kucet.ac.in",
        role=UserRole.STUDENT,
        department_id=seed_data["department"].id,
        hashed_password="pw",
        is_active=True,
    )
    db_session.add(student_user)
    db_session.commit()

    from app.core.security import create_access_token
    token = create_access_token(
        subject=student_user.id,
        role=student_user.role.value,
        additional_claims={"email": student_user.email, "department_id": seed_data["department"].id},
    )

    # Calling with limit=0 emits connection greeting and closes cleanly
    response = client.get(
        f"/api/v1/events/stream?channels=user:{student_user.id}&limit=0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert ": connected" in response.text


def test_sse_endpoint_authorized_channel_with_query_token(client, seed_data, db_session):
    student_user = User(
        email="sse_student3@kucet.ac.in",
        role=UserRole.STUDENT,
        department_id=seed_data["department"].id,
        hashed_password="pw",
        is_active=True,
    )
    db_session.add(student_user)
    db_session.commit()

    from app.core.security import create_access_token
    token = create_access_token(
        subject=student_user.id,
        role=student_user.role.value,
        additional_claims={"email": student_user.email, "department_id": seed_data["department"].id},
    )

    # Browser EventSource queries token parameter
    response = client.get(
        f"/api/v1/events/stream?channels=user:{student_user.id}&limit=0&token={token}"
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert ": connected" in response.text
