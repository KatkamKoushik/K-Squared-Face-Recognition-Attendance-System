"""
K² FRS — Real-Time Event Broadcaster Service.
Manages subscription queues, replay buffer for reconnection, and authenticated fan-out.
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.domain.enums import UserRole
from app.domain.models.academic import SubjectOffering, User
from app.domain.models.session import AttendanceSession
from app.schemas.events import EventMessage, RealtimeEventType


class EventBroadcaster:
    """In-process and database-backed transactional real-time event broadcaster."""

    def __init__(self, buffer_size: int = 1000):
        self._subscribers: Set[asyncio.Queue] = set()
        self._history: deque[EventMessage] = deque(maxlen=buffer_size)
        self._lock = asyncio.Lock()

    def _write_outbox(self, event: EventMessage, db: Session) -> None:
        """Persist event to transactional outbox table inside current database transaction."""
        try:
            from app.domain.models.outbox import OutboxEvent
            outbox_entry = OutboxEvent(
                id=event.event_id,
                event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                channel=event.channel,
                payload=event.payload,
                created_at=event.timestamp,
                is_published=True,
                published_at=event.timestamp,
            )
            db.add(outbox_entry)
            db.flush()
        except Exception:
            # Outbox persistence failure should not crash business transaction
            pass

    async def publish(self, event: EventMessage, db: Optional[Session] = None) -> None:
        """Publish an event to the replay buffer, outbox, and all active subscriber queues."""
        if db is not None:
            self._write_outbox(event, db)

        async with self._lock:
            self._history.append(event)
            dead_queues = set()
            for q in self._subscribers:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop slow subscribers
                    dead_queues.add(q)
            self._subscribers.difference_update(dead_queues)

    def publish_sync(self, event: EventMessage, db: Optional[Session] = None) -> None:
        """Synchronous wrapper to safely publish from non-async SQLAlchemy service calls."""
        if db is not None:
            self._write_outbox(event, db)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event))
        except RuntimeError:
            # If no running loop (e.g. background worker thread), append directly to history
            self._history.append(event)

    async def subscribe(
        self,
        allowed_channels: Set[str],
        last_event_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> AsyncGenerator[EventMessage, None]:
        """Subscribe to events matching allowed_channels, replaying from last_event_id if provided."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)

        async with self._lock:
            self._subscribers.add(q)

            # Replay missed events if last_event_id is specified
            if last_event_id:
                replayed_ids = set()
                # 1. Attempt to replay from database outbox if db session is provided
                if db is not None:
                    try:
                        from app.domain.models.outbox import OutboxEvent
                        target_ev = db.query(OutboxEvent).filter(OutboxEvent.id == last_event_id).first()
                        query = db.query(OutboxEvent)
                        if target_ev:
                            query = query.filter(
                                (OutboxEvent.created_at > target_ev.created_at) |
                                ((OutboxEvent.created_at >= target_ev.created_at) & (OutboxEvent.id != target_ev.id))
                            )
                        query = query.order_by(OutboxEvent.created_at.asc()).limit(100)
                        for row in query.all():
                            if row.channel in allowed_channels or "all" in allowed_channels:
                                try:
                                    ev_type = RealtimeEventType(row.event_type)
                                except ValueError:
                                    ev_type = RealtimeEventType.SESSION_STATE_CHANGED
                                ev_msg = EventMessage(
                                    event_id=row.id,
                                    event_type=ev_type,
                                    timestamp=row.created_at,
                                    channel=row.channel,
                                    payload=row.payload,
                                )
                                await q.put(ev_msg)
                                replayed_ids.add(row.id)
                    except Exception:
                        pass

                # 2. Replay from in-memory ring buffer for any events not in DB or if DB is absent
                replay_started = False
                for historical_event in self._history:
                    if historical_event.event_id in replayed_ids:
                        continue
                    if replay_started:
                        if historical_event.channel in allowed_channels or "all" in allowed_channels:
                            await q.put(historical_event)
                    elif historical_event.event_id == last_event_id:
                        replay_started = True

        try:
            while True:
                event = await q.get()
                if event.channel in allowed_channels or "all" in allowed_channels:
                    yield event
        finally:
            async with self._lock:
                self._subscribers.discard(q)


# Global singleton instance
broadcaster = EventBroadcaster()


def validate_channel_subscription(user: User, channel: str, db: Session) -> bool:
    """
    Validate whether the given user has permission to subscribe to a specific channel.
    Channels:
    - user:{user_id} -> Accessible if user.id == user_id
    - department:{dept_id} -> Accessible if user is in dept_id or is SUPER_ADMIN / DEVELOPER
    - session:{session_id} -> Accessible if user is assigned faculty or admin in session's department or SUPER_ADMIN
    - global:admin -> Accessible strictly to SUPER_ADMIN or DEVELOPER
    """
    if user.role in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN):
        return True

    if channel.startswith("user:"):
        target_uid = channel.split(":", 1)[1]
        return user.id == target_uid

    if channel.startswith("department:"):
        if user.role not in (UserRole.DEVELOPER, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.FACULTY):
            return False
        target_dept_id = channel.split(":", 1)[1]
        return user.department_id is not None and user.department_id == target_dept_id

    if channel.startswith("session:"):
        session_id = channel.split(":", 1)[1]
        session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
        if not session:
            return False

        # If user is faculty, must be session conductor
        if user.role == UserRole.FACULTY:
            if session.faculty_id and user.faculty_profile:
                return session.faculty_id == user.faculty_profile.id
            return False

        # If user is admin, offering department must match user department
        if user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            offering = db.query(SubjectOffering).filter(SubjectOffering.id == session.offering_id).first()
            if offering and offering.subject:
                return user.department_id is not None and offering.subject.department_id == user.department_id
            return False

        return False

    if channel == "global:admin":
        return False

    return False
