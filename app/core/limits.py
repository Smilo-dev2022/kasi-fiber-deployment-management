from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.responses import JSONResponse


limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])  # global default


def rate_limit_handler(request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

