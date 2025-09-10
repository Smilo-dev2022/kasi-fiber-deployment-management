import uuid
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        tenant_id = request.headers.get("X-Tenant-Id") or "default"
        user_id = request.headers.get("X-User-Id") or None
        request.state.request_id = request_id
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

