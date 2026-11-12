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
    """In-process real-time event broadcaster supporting SSE and replay buffers."""

    def __init__(self, buffer_size: int = 1000):
        self._subscribers: Set[asyncio.Queue] = set()
        self._history: deque[EventMessage] = deque(maxlen=buffer_size)
        self._lock = asyncio.Lock()

    async def publish(self, event: EventMessage) -> None:
        """Publish an event to the replay buffer and all active subscriber queues."""
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

    def publish_sync(self, event: EventMessage) -> None:
        """Synchronous wrapper to safely publish from non-async SQLAlchemy service calls."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event))
        except RuntimeError:
            # If no running loop (e.g. background worker thread), append directly to history
            self._history.append(event)

    async def subscribe(
        self,
        allowed_channels: Set[str],
        last_event_id: Optional[str] = None
    ) -> AsyncGenerator[EventMessage, None]:
        """Subscribe to events matching allowed_channels, replaying from last_event_id if provided."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)

        async with self._lock:
            self._subscribers.add(q)

            # Replay missed events if last_event_id is specified
            if last_event_id:
                replay_started = False
                for historical_event in self._history:
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
