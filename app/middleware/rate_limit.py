import time
import os
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class WebhookRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int | None = None) -> None:
        super().__init__(app)
        self._limit = limit_per_minute or int(os.getenv("WEBHOOKS_RATE_PER_MIN", "60"))
        self._buckets: dict[str, tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = request.url.path
        if path.startswith("/webhooks") and self._limit > 0:
            now = time.time()
            window = int(now // 60)
            ip = request.client.host if request.client else "unknown"
            key = f"{ip}:{window}"
            ts, count = self._buckets.get(key, (now, 0))
            if ts != now and int(ts // 60) != window:
                ts, count = now, 0
            if count >= self._limit:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
            self._buckets[key] = (ts, count + 1)
        return await call_next(request)

