import os
from typing import Generator, Callable, Sequence

from fastapi import Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Default to SQLite for local/dev/testing to avoid external deps
    "sqlite:///./app.db",
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, future=True, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, future=True)
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


def require_tenant(optional: bool = False) -> Callable:
    async def checker(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id")):
        if not x_tenant_id and not optional:
            raise HTTPException(status_code=400, detail="X-Tenant-Id required")
        return x_tenant_id

    return checker

