import time
from fastapi import Request, HTTPException
from app.core.redis_client import get_redis


def limiter(limit: int, window_sec: int, key_fn=None):
    async def _limiter(request: Request):
        r = await get_redis()
        now = int(time.time())
        key_base = await key_fn(request) if key_fn else (request.client.host if request.client else "unknown")
        key = f"ratelimit:{key_base}:{now//window_sec}:{window_sec}:{limit}"
        cur = await r.incr(key)
        if cur == 1:
            await r.expire(key, window_sec)
        if cur > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return _limiter


async def key_by_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def key_by_org(request: Request) -> str:
    return getattr(request.state, "org_id", request.client.host if request.client else "unknown")

