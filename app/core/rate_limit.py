import time
from collections import deque
from threading import Lock
from typing import Callable
from fastapi import Header, HTTPException
import os

_redis_client = None
try:
    import redis

    _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_client = redis.from_url(_redis_url)
except Exception:
    _redis_client = None


_buckets: dict[str, deque[float]] = {}
_locks: dict[str, Lock] = {}


def rate_limit(namespace: str, max_requests: int, per_seconds: int) -> Callable:
    def _dep(x_forwarded_for: str | None = Header(default=None, alias="X-Forwarded-For"), x_real_ip: str | None = Header(default=None, alias="X-Real-IP")):
        # Derive client IP; prefer forwarded headers
        client_ip = None
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
        elif x_real_ip:
            client_ip = x_real_ip.strip()
        else:
            client_ip = "unknown"
        key = f"rate:{namespace}:{client_ip}"
        now = int(time.time())
        window_start = now - per_seconds

        if _redis_client:
            # Use Redis sorted set for sliding window
            try:
                pipe = _redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                removed, count = pipe.execute()
                if count >= max_requests:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                _redis_client.zadd(key, {str(now): now})
                _redis_client.expire(key, per_seconds)
            except Exception:
                # Fallback to memory if Redis hiccups
                pass

        if not _redis_client:
            lock = _locks.setdefault(key, Lock())
            with lock:
                dq = _buckets.setdefault(key, deque())
                # Drop old entries
                while dq and dq[0] < window_start:
                    dq.popleft()
                if len(dq) >= max_requests:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                dq.append(now)
        return True

    return _dep

