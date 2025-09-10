import os
from typing import Generator, Callable, Sequence

from fastapi import Header, HTTPException
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
    async def checker(x_role: str | None = Header(default=None, alias="X-Role")):
        if allowed_roles and x_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker


def get_db_session() -> Session:
    return SessionLocal()

