import os
import redis.asyncio as redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def ping_redis() -> bool:
    r = await get_redis()
    try:
        pong = await r.ping()
        return bool(pong)
    except Exception:
        return False

