import json
import asyncio
from typing import Any, Optional

from app.core.redis_client import get_redis


def cache_get(key: str) -> Optional[Any]:
    try:
        r = asyncio.run(get_redis())
        val = asyncio.run(r.get(key))
        if val is None:
            return None
        try:
            return json.loads(val)
        except Exception:
            return val
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 30) -> None:
    try:
        r = asyncio.run(get_redis())
        payload = json.dumps(value) if not isinstance(value, (bytes, bytearray, str)) else value
        asyncio.run(r.setex(key, ttl_seconds, payload))
    except Exception:
        pass

