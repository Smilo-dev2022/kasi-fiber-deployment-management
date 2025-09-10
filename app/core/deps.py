import os
from typing import Generator, Callable, Sequence, Optional, Dict, Any

from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import jwt


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


JWT_SECRET = os.getenv("JWT_SECRET", None)
JWT_ALG = os.getenv("JWT_ALGORITHM", "HS256")


def _decode_jwt_token(token: str) -> Dict[str, Any]:
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT not configured")
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_claims(authorization: Optional[str] = Header(default=None, alias="Authorization")) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    claims = _decode_jwt_token(token)
    return claims


def require_roles(*allowed_roles: Sequence[str]) -> Callable:
    async def checker(claims: Dict[str, Any] = Depends(get_claims)):
        if not allowed_roles:
            return True
        roles = claims.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]
        if not any(r in roles for r in allowed_roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker

