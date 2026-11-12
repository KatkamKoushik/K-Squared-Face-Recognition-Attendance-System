"""
FRS V7.1 K² — Real-Time Event Synchronization Schemas.
Enforces typed real-time event payloads across SSE and WebSocket streams.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class RealtimeEventType(str, Enum):
    SESSION_STATE_CHANGED = "SESSION_STATE_CHANGED"
    FRAME_PROCESSED = "FRAME_PROCESSED"
    PROPOSAL_READY = "PROPOSAL_READY"
    RECEIPT_ISSUED = "RECEIPT_ISSUED"
    ENROLLMENT_SUBMITTED = "ENROLLMENT_SUBMITTED"
    ENROLLMENT_DECIDED = "ENROLLMENT_DECIDED"
    ATTENDANCE_APPEALED = "ATTENDANCE_APPEALED"
    ATTENDANCE_APPEAL_REVIEWED = "ATTENDANCE_APPEAL_REVIEWED"
    CORRECTION_SUBMITTED = "CORRECTION_SUBMITTED"
    CORRECTION_REVIEWED = "CORRECTION_REVIEWED"
    DASHBOARD_STATS_UPDATED = "DASHBOARD_STATS_UPDATED"


class EventMessage(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: RealtimeEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    channel: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> str:
        """Format as SSE compliant data packet."""
        iso_time = self.timestamp.isoformat()
        import json
        data = json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": iso_time,
            "channel": self.channel,
            "payload": self.payload
        })
        return f"id: {self.event_id}\nevent: {self.event_type.value}\ndata: {data}\n\n"
