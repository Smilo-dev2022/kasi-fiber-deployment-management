import os
from typing import Generator, Callable, Sequence

from fastapi import Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://app:app@localhost:5432/app",
)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
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

