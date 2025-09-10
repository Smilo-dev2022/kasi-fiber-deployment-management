from typing import Callable
from sqlalchemy.orm import Session
from app.database import SessionLocal


def get_db() -> Session:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_roles(*_roles: str) -> Callable[[], None]:
    # Placeholder authorization dependency. Replace with real auth/role checks.
    def _dependency() -> None:
        return None

    return _dependency
