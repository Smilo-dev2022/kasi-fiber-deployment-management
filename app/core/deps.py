import os
from typing import Generator, Callable, Sequence

from fastapi import Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.models.user import User


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Default useful for local dev; override in production
    "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
)

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


def get_current_user(x_org_id: str | None = Header(default=None, alias="X-Org-Id")) -> User:
    from uuid import UUID

    org_uuid = None
    if x_org_id:
        try:
            org_uuid = UUID(x_org_id)
        except Exception:
            org_uuid = None
    return User(org_id=org_uuid)

