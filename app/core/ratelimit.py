import time
from typing import Dict, Tuple
from fastapi import HTTPException


class SlidingWindowRateLimiter:
    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: Dict[Tuple[str, str], list[float]] = {}

    def allow(self, key: Tuple[str, str]) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        bucket = self._events.setdefault(key, [])
        # Drop old
        while bucket and bucket[0] < window_start:
            bucket.pop(0)
        if len(bucket) >= self.max_events:
            return False
        bucket.append(now)
        return True


global_webhook_limiter = SlidingWindowRateLimiter(max_events=120, window_seconds=60)


def enforce_webhook_rate_limit(ip: str, route: str):
    if not global_webhook_limiter.allow((ip, route)):
        raise HTTPException(status_code=429, detail="Too Many Requests")

