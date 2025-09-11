import os
from typing import Generator, Callable, Sequence, Optional, Dict, Any

from fastapi import Header, HTTPException, Depends
import jwt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://app:app@localhost:5432/app",
)

# Add basic connection retries on startup to handle container orchestration timing
def _create_engine_with_retries(url: str):
    import time
    last_error: Exception | None = None
    for attempt in range(1, 11):
        try:
            engine = create_engine(url, future=True)
            # test connection quickly
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception as e:  # noqa: BLE001
            last_error = e
            time.sleep(2)
    if last_error:
        raise last_error
    return create_engine(url, future=True)

engine = _create_engine_with_retries(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_roles(*allowed_roles: Sequence[str]) -> Callable:
    async def checker(user: Dict[str, Any] = Depends(lambda: get_current_user(required=True))):
        role = user.get("role") if user else None
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker


def get_db_session() -> Session:
    return SessionLocal()


def get_current_user(required: bool = False) -> Optional[Dict[str, Any]]:
    """Parse and verify JWT from Authorization header and return user claims.

    Expects 'Authorization: Bearer <token>' or 'X-Auth-Token'.
    In non-required mode returns None if missing/invalid. In required mode raises 401.
    """
    import os
    from fastapi import Request
    from fastapi import status
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    try:
        # Retrieve current request via dependency injection hack
        from fastapi import Request as FastAPIRequest  # type: ignore
    except Exception:
        FastAPIRequest = None  # type: ignore

    # Use global request from contextvar if set by middleware
    try:
        from contextvars import ContextVar
        _req_var: ContextVar = globals().get("_request_ctx")  # type: ignore
        request: Optional[StarletteRequest] = _req_var.get() if _req_var else None  # type: ignore
    except Exception:
        request = None

    if not request:
        # Fallback: cannot read headers; allow through if not required
        if required:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return None

    auth = request.headers.get("Authorization") or ""
    token = None
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    token = token or request.headers.get("X-Auth-Token")

    if not token:
        if required:
            raise HTTPException(status_code=401, detail="Missing token")
        return None

    secret = os.getenv("JWT_SECRET")
    if not secret:
        # Don't leak misconfiguration details to clients
        raise HTTPException(status_code=500, detail="Server configuration error")

    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])  # adjust alg as needed
        # Normalize fields
        role = claims.get("role") or claims.get("roles", [None])[0]
        org_id = claims.get("org_id") or claims.get("org")
        return {"sub": claims.get("sub"), "role": role, "org_id": org_id, "claims": claims}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

