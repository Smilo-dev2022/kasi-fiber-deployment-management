import time
from collections import deque
from threading import Lock
from typing import Callable
from fastapi import Header, HTTPException
import os
import time
import redis


_buckets: dict[str, deque[float]] = {}
_locks: dict[str, Lock] = {}
_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client = None
try:
    _redis_client = redis.Redis.from_url(_redis_url)
    _redis_client.ping()
except Exception:
    _redis_client = None


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
        # Prefer Redis fixed window if available
        if _redis_client is not None:
            window_id = int(time.time() // per_seconds)
            key = f"rl:{namespace}:{client_ip}:{window_id}"
            try:
                count = _redis_client.incr(key)
                if count == 1:
                    _redis_client.expire(key, per_seconds)
                if count > max_requests:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                return True
            except Exception:
                # Fallback to in-memory if Redis hiccups
                pass

        key = f"{namespace}:{client_ip}"
        now = time.time()
        window_start = now - per_seconds

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

