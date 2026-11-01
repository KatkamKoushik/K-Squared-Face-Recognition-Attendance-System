"""
FRS V7.1 K² — Rate Limiter & Abuse Prevention Test Suite.
Verifies sliding-window throttling, burst protection, retry-after calculations,
route exemptions, and timestamp window purging.
"""

import time
import pytest
from starlette.testclient import TestClient
from app.core.rate_limiter import SlidingWindowRateLimiter
from app.main import create_application


@pytest.fixture
def fresh_limiter():
    """Create an isolated rate limiter instance for testing."""
    return SlidingWindowRateLimiter(requests_per_minute=10, burst_limit=3)


def test_sliding_window_allows_normal_traffic(fresh_limiter):
    """Under-limit requests should all pass without being rate limited."""
    for _ in range(3):
        limited, retry_after = fresh_limiter.is_rate_limited("10.0.0.1")
        assert not limited
        assert retry_after == 0


def test_burst_limit_triggering(fresh_limiter):
    """Exceeding burst limit within 1 second triggers rate limiting."""
    # 3 requests allowed by burst limit
    for _ in range(3):
        limited, _ = fresh_limiter.is_rate_limited("10.0.0.2")
        assert not limited

    # 4th immediate request must be burst-limited
    limited, retry_after = fresh_limiter.is_rate_limited("10.0.0.2")
    assert limited
    assert retry_after == 1


def test_window_limit_triggering():
    """Exceeding the total requests-per-minute triggers rate limiting with positive retry_after."""
    limiter = SlidingWindowRateLimiter(requests_per_minute=5, burst_limit=10)
    ip = "10.0.0.3"

    for _ in range(5):
        limited, _ = limiter.is_rate_limited(ip)
        assert not limited

    # 6th request must exceed window
    limited, retry_after = limiter.is_rate_limited(ip)
    assert limited
    assert retry_after > 0


def test_ip_isolation(fresh_limiter):
    """Rate limits on one IP must not affect requests from another IP."""
    ip1 = "10.0.0.10"
    ip2 = "10.0.0.20"

    # Exhaust burst limit for ip1
    for _ in range(3):
        fresh_limiter.is_rate_limited(ip1)
    limited_ip1, _ = fresh_limiter.is_rate_limited(ip1)
    assert limited_ip1

    # ip2 must remain unrestricted
    limited_ip2, _ = fresh_limiter.is_rate_limited(ip2)
    assert not limited_ip2


def test_old_entries_cleanup():
    """Timestamps older than 60 seconds are purged."""
    limiter = SlidingWindowRateLimiter(requests_per_minute=10, burst_limit=5)
    ip = "10.0.0.5"

    # Inject simulated timestamps older than 60 seconds
    now = time.time()
    limiter._history[ip] = [now - 70.0, now - 65.0, now]
    limiter._last_cleanup = now - 35.0  # Force cleanup on next call

    limited, _ = limiter.is_rate_limited(ip)
    assert not limited
    # Only recent timestamps must remain
    assert all(t > now - 60.0 for t in limiter._history[ip])


def test_rate_limiting_middleware_route_exemptions():
    """Health endpoints, docs, and OpenAPI must be exempt from rate limiting."""
    app = create_application()
    client = TestClient(app)

    # Health endpoints must return 200 even under repeated rapid fire
    for _ in range(15):
        resp = client.get("/api/v1/health/liveness")
        assert resp.status_code == 200

        resp_metrics = client.get("/api/v1/health/metrics")
        assert resp_metrics.status_code == 200
