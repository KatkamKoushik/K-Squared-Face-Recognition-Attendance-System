"""
FRS V7.1 K² — Real-Time Server-Sent Events (SSE) Route.
Provides authenticated, department-isolated live event streams with reconnect replay.
"""

import asyncio
from typing import Optional, Set
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.domain.models.academic import User
from app.services.event_broadcaster import broadcaster, validate_channel_subscription

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/stream", summary="Subscribe to real-time institutional event stream (SSE)")
async def stream_events(
    channels: str = Query(..., description="Comma-separated list of channels to subscribe to"),
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    query_last_event_id: Optional[str] = Query(None, alias="last_event_id"),
    limit: Optional[int] = Query(None, ge=0, description="Optional maximum number of events to receive"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Establish an authenticated Server-Sent Events (SSE) connection.
    Validates subscription authorization against user role and department isolation rules.
    """
    effective_last_event_id = last_event_id or query_last_event_id
    requested_channels: Set[str] = {c.strip() for c in channels.split(",") if c.strip()}

    if not requested_channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one channel must be specified."
        )

    # Validate permissions for each channel
    for channel in requested_channels:
        if not validate_channel_subscription(current_user, channel, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to subscribe to channel: {channel}"
            )

    async def event_generator():
        # Emit initial connected greeting
        yield ": connected\n\n"
        if limit is not None and limit <= 0:
            return

        count = 0
        subscription = broadcaster.subscribe(
            allowed_channels=requested_channels,
            last_event_id=effective_last_event_id
        )

        try:
            async for event in subscription:
                yield event.to_sse()
                count += 1
                if limit is not None and count >= limit:
                    break
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
