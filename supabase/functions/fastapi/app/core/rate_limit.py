"""Deprecated in-memory rate limiter; use app.core.limiter with Redis instead."""

from typing import Callable


def rate_limit(namespace: str, max_requests: int, per_seconds: int) -> Callable:  # pragma: no cover
    def _dep():
        return True

    return _dep

