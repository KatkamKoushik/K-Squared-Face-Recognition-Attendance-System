"""
FRS V7.1 K² — Ingress Rate Limiting & Abuse Prevention Middleware.
Implements bounded sliding-window rate limiting per client IP to safeguard
against brute force, credential stuffing, and photo-batch ingestion floods.
Conforms to Checklist Section 6, 11, and 31.
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.schemas.common import ErrorEnvelope, ErrorDetail


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding-window rate limiter maintaining timestamps in memory.
    Automatically purges expired windows on ingress.
    """

    def __init__(self, requests_per_minute: int = 120, burst_limit: int = 40):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        # Storage: ip -> list of float timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup_old_entries(self, now: float):
        """Purge entries older than 60 seconds every 30 seconds."""
        if now - self._last_cleanup > 30.0:
            threshold = now - 60.0
            for ip in list(self._history.keys()):
                self._history[ip] = [t for t in self._history[ip] if t > threshold]
                if not self._history[ip]:
                    del self._history[ip]
            self._last_cleanup = now

    def is_rate_limited(self, ip: str) -> Tuple[bool, int]:
        """
        Check if an IP has exceeded rate thresholds.
        Returns: (is_limited: bool, retry_after_seconds: int)
        """
        now = time.time()
        self._cleanup_old_entries(now)

        window_start = now - 60.0
        burst_start = now - 1.0

        timestamps = [t for t in self._history[ip] if t > window_start]
        self._history[ip] = timestamps

        # 1. Check 1-second burst limit
        recent_burst = sum(1 for t in timestamps if t > burst_start)
        if recent_burst >= self.burst_limit:
            return True, 1

        # 2. Check 60-second window limit
        if len(timestamps) >= self.requests_per_minute:
            oldest_in_window = timestamps[0]
            retry_after = max(1, int(60.0 - (now - oldest_in_window)))
            return True, retry_after

        # Record this request
        self._history[ip].append(now)
        return False, 0


# Global instance
rate_limiter = SlidingWindowRateLimiter(requests_per_minute=240, burst_limit=50)


async def rate_limiting_middleware(request: Request, call_next):
    # Exempt internal health and documentation routes
    path = request.url.path
    if (
        path.startswith("/docs")
        or path.startswith("/redoc")
        or path.startswith("/openapi.json")
        or path.endswith("/liveness")
        or path.endswith("/readiness")
        or path.endswith("/metrics")
    ):
        return await call_next(request)

    client_ip = request.client.host if request.client else "127.0.0.1"
    limited, retry_after = rate_limiter.is_rate_limited(client_ip)

    if limited:
        corr_id = getattr(request.state, "correlation_id", "rate-limit")
        envelope = ErrorEnvelope(
            error=ErrorDetail(
                code="TOO_MANY_REQUESTS",
                message=f"Rate limit exceeded. Too many requests from client {client_ip}.",
                reason_code="RATE_LIMIT_EXCEEDED",
                details={"retry_after_seconds": retry_after},
            ),
            correlation_id=corr_id,
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=envelope.model_dump(mode="json"),
            headers={"Retry-After": str(retry_after)},
        )

    return await call_next(request)

