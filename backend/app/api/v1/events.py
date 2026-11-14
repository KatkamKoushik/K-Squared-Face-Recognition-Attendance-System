"""
K² FRS — Real-Time Server-Sent Events (SSE) Route.
Provides authenticated, department-isolated live event streams with reconnect replay.
"""

import asyncio
from typing import Optional, Set
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, security_scheme
from app.core.errors import AuthenticationError
from app.core.security import verify_token
from app.domain.models.academic import User
from app.services.event_broadcaster import broadcaster, validate_channel_subscription

router = APIRouter(prefix="/events", tags=["events"])


def get_sse_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    token: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticates SSE stream subscribers.
    Permits URL token query parameters specifically for browser EventSource API,
    which does not support custom HTTP Authorization headers in standard HTML5.
    """
    raw_token = auth.credentials if (auth and auth.credentials) else token
    if not raw_token or raw_token in ("null", "undefined"):
        raise AuthenticationError(
            "Authorization header or token query parameter required for SSE connection",
            reason_code="TOKEN_MISSING",
        )

    payload = verify_token(raw_token)
    user_id = payload.get("user_id") or payload.get("sub")
    email = payload.get("email")

    user = None
    if user_id:
        user = db.get(User, user_id)
    if not user and email:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User is inactive or not found", reason_code="USER_NOT_ACTIVE")

    token_ver = payload.get("token_version")
    if token_ver is not None and token_ver != user.token_version:
        raise AuthenticationError("Session has been revoked or expired. Please log in again.", reason_code="TOKEN_REVOKED")

    return user


@router.get("/stream", summary="Subscribe to real-time institutional event stream (SSE)")
async def stream_events(
    channels: str = Query(..., description="Comma-separated list of channels to subscribe to"),
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    query_last_event_id: Optional[str] = Query(None, alias="last_event_id"),
    limit: Optional[int] = Query(None, ge=0, description="Optional maximum number of events to receive"),
    current_user: User = Depends(get_sse_current_user),
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
