from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._store[key]
        self._store[key] = [t for t in timestamps if t > window_start]
        if len(self._store[key]) >= self.max_requests:
            return False
        self._store[key].append(now)
        return True

    def seconds_until_reset(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = [t for t in self._store[key] if t > window_start]
        if not timestamps:
            return 0
        oldest = min(timestamps)
        return max(0, int(self.window_seconds - (now - oldest)) + 1)


# Istanze globali
anon_limiter = RateLimiter(max_requests=20, window_seconds=3600)   # 20/ora per IP
user_limiter = RateLimiter(max_requests=30, window_seconds=3600)   # 30/ora per user
