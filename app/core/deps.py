import os
from typing import Generator, Callable, Sequence

from fastapi import Header, HTTPException, Request
from sqlalchemy import create_engine, text
from app.core.auth import decode_bearer_token, extract_role_from_claims
from sqlalchemy.orm import declarative_base, sessionmaker, Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://app:app@localhost:5432/app",
)

# Allow local development to skip eager DB connectivity checks so the API can boot
# even when a database service is not available (e.g., limited CI or sandbox).
DB_SKIP_STARTUP_TESTS = os.getenv("DB_SKIP_STARTUP_TESTS", "false").lower() in ("1", "true", "yes")

# Add basic connection retries on startup to handle container orchestration timing
def _create_engine_with_retries(url: str):
    import time
    if DB_SKIP_STARTUP_TESTS:
        # Create engine without testing connectivity; connections will be attempted lazily
        return create_engine(url, future=True)

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
    async def checker(request: Request, x_role: str | None = Header(default=None, alias="X-Role")):
        # Prefer Authorization bearer token if present
        claims = decode_bearer_token(request.headers.get("Authorization"))
        effective_role = extract_role_from_claims(claims) if claims else None
        if not effective_role:
            effective_role = x_role
        if allowed_roles and effective_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        # Attach claims to request.state for downstream use
        if claims:
            setattr(request.state, "jwt_claims", claims)
        return True

    return checker


def get_db_session() -> Session:
    return SessionLocal()

