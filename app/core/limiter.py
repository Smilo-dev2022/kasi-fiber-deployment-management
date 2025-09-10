import time
from fastapi import Request, HTTPException
from app.core.redis_client import get_redis


def limiter(limit: int, window_sec: int, key_fn=None):
    async def _limiter(request: Request):
        r = await get_redis()
        now = int(time.time())
        key_base = (
            await key_fn(request)
            if key_fn
            else (_client_ip_from_headers(request) or (request.client.host if request.client else "unknown"))
        )
        key = f"ratelimit:{key_base}:{now//window_sec}:{window_sec}:{limit}"
        cur = await r.incr(key)
        if cur == 1:
            await r.expire(key, window_sec)
        if cur > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return _limiter


def _client_ip_from_headers(request: Request) -> str | None:
    # Prefer proxy headers when present
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # first IP in list
        return xff.split(",")[0].strip()
    xri = request.headers.get("X-Real-IP")
    if xri:
        return xri.strip()
    return None


async def key_by_ip(request: Request) -> str:
    return _client_ip_from_headers(request) or (request.client.host if request.client else "unknown")


async def key_by_org(request: Request) -> str:
    # Prefer explicit header, then request.state.org_id, fallback to IP
    org_id = request.headers.get("X-Org-Id") or getattr(request.state, "org_id", None)
    if org_id:
        return f"org:{org_id}"
    ip = _client_ip_from_headers(request) or (request.client.host if request.client else "unknown")
    return f"ip:{ip}"

