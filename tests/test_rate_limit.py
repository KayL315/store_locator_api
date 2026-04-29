import pytest
from fastapi import HTTPException

from rate_limit import InMemoryRateLimiter


def test_rate_limiter_allows_requests():
    limiter = InMemoryRateLimiter()

    for _ in range(5):
        limiter.check_rate_limit("127.0.0.1")

    assert len(limiter.requests["127.0.0.1"]) == 5


def test_rate_limiter_blocks_after_10_per_minute():
    limiter = InMemoryRateLimiter()

    for _ in range(10):
        limiter.check_rate_limit("127.0.0.1")

    with pytest.raises(HTTPException) as exc:
        limiter.check_rate_limit("127.0.0.1")

    assert exc.value.status_code == 429
    assert "10 requests per minute" in exc.value.detail