import os
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
    # Prefer org from JWT claims attached by middleware/deps
    org_id = getattr(request.state, "org_id", None)
    if org_id:
        return f"org:{org_id}"
    return request.client.host if request.client else "unknown"


def env_ip_limiter(env_prefix: str = "WEBHOOK_IP", default_limit: int = 60, default_window: int = 60):
    """Create a limiter keyed by client IP with limits sourced from env.

    Expects env vars like "{PREFIX}_LIMIT" and "{PREFIX}_WINDOW".
    """
    limit = int(os.getenv(f"{env_prefix}_LIMIT", default_limit))
    window = int(os.getenv(f"{env_prefix}_WINDOW", default_window))
    return limiter(limit=limit, window_sec=window, key_fn=key_by_ip)


def env_org_limiter(env_prefix: str = "HEAVY_ORG", default_limit: int = 120, default_window: int = 60):
    """Create a limiter keyed by org id with optional role bypass.

    - Limits sourced from env: "{PREFIX}_LIMIT" and "{PREFIX}_WINDOW"
    - Bypass roles from env: "{PREFIX}_BYPASS_ROLES" (comma-separated), defaults to "NOC"
    """
    limit = int(os.getenv(f"{env_prefix}_LIMIT", default_limit))
    window = int(os.getenv(f"{env_prefix}_WINDOW", default_window))
    bypass_roles = [r.strip() for r in os.getenv(f"{env_prefix}_BYPASS_ROLES", "NOC").split(",") if r.strip()]

    async def _dep(request: Request):
        # Prefer JWT role from middleware-attached claims
        claims = getattr(request.state, "jwt_claims", None)
        role = (claims or {}).get("role") or request.headers.get("X-Role")
        if role and role in bypass_roles:
            return
        await limiter(limit=limit, window_sec=window, key_fn=key_by_org)(request)

    return _dep

