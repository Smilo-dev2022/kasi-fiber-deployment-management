import os
from typing import Generator, Callable, Sequence, Optional, Any, Dict

import jwt
from fastapi import Header, HTTPException, Request, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


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


def _decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    secrets = [os.getenv("JWT_SECRET"), os.getenv("JWT_PREV_SECRET")]
    algorithms = ["HS256", "HS384", "HS512"]
    for secret in secrets:
        if not secret:
            continue
        for alg in algorithms:
            try:
                return jwt.decode(token, secret, algorithms=[alg], options={"verify_aud": False})
            except Exception:
                continue
    return None


def get_current_user() -> Callable:
    async def dependency(request: Request, authorization: str | None = Header(default=None, alias="Authorization")):
        token = None
        role = request.headers.get("X-Role")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
        claims = _decode_jwt_token(token) if token else None
        user = {
            "id": (claims.get("sub") if claims else None) or request.headers.get("X-User-Id"),
            "role": (claims.get("role") if claims else role),
            "claims": claims or {},
        }
        return user

    return dependency


def require_roles(*allowed_roles: Sequence[str]) -> Callable:
    async def checker(user: dict = Depends(get_current_user())):
        role = user.get("role") if user else None
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker

