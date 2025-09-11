import os
from typing import Generator, Callable, Sequence, Optional

from fastapi import HTTPException, Request, Depends
from sqlalchemy import create_engine, text
from app.core.auth import (
    decode_bearer_token,
    extract_role_from_claims,
    extract_org_from_claims,
    extract_tenant_from_claims,
)
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
    async def checker(request: Request):
        claims = decode_bearer_token(request.headers.get("Authorization"))
        if not claims:
            raise HTTPException(status_code=401, detail="Unauthorized")
        effective_role = extract_role_from_claims(claims) if claims else None
        if allowed_roles and effective_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        # Attach claims to request.state for downstream use
        setattr(request.state, "jwt_claims", claims)
        # Also surface parsed org/tenant to request.state for convenience
        org_id = extract_org_from_claims(claims)
        tenant_id = extract_tenant_from_claims(claims)
        if org_id:
            setattr(request.state, "org_id", org_id)
        if tenant_id:
            setattr(request.state, "tenant_id", tenant_id)
        return True

    return checker


def get_claims(request: Request) -> dict:
    claims = getattr(request.state, "jwt_claims", None)
    if claims is None:
        claims = decode_bearer_token(request.headers.get("Authorization"))
        if claims:
            setattr(request.state, "jwt_claims", claims)
    return claims or {}


def require_org(request: Request = None) -> str:
    if request is None:
        raise HTTPException(status_code=500, detail="Request context unavailable")
    claims = get_claims(request)
    org_id: Optional[str] = extract_org_from_claims(claims)
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization scope missing in token")
    setattr(request.state, "org_id", org_id)
    return org_id


def get_db_session() -> Session:
    return SessionLocal()

