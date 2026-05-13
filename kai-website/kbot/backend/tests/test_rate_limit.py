import time
import pytest
from app.rate_limit import RateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("key1") is True
    assert limiter.is_allowed("key1") is True
    assert limiter.is_allowed("key1") is True


def test_rate_limiter_blocks_over_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.is_allowed("key2")
    limiter.is_allowed("key2")
    assert limiter.is_allowed("key2") is False


def test_rate_limiter_different_keys_independent():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("keyA")
    assert limiter.is_allowed("keyA") is False
    assert limiter.is_allowed("keyB") is True


def test_rate_limiter_seconds_until_reset_positive_when_blocked():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("key3")
    limiter.is_allowed("key3")
    secs = limiter.seconds_until_reset("key3")
    assert secs > 0
    assert secs <= 60
