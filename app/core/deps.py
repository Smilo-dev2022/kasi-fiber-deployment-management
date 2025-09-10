import os
from typing import Generator, Callable, Sequence

from fastapi import Header, HTTPException, Request
from sqlalchemy import create_engine, text
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


def require_roles(*allowed_roles: Sequence[str]) -> Callable:
    async def checker(x_role: str | None = Header(default=None, alias="X-Role")):
        if allowed_roles and x_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker


def get_tenant_id_from_request(request: Request, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id")) -> str:
    host = request.headers.get("host", "").split(":")[0]
    # Prefer explicit header, else resolve by domain
    if x_tenant_id:
        return x_tenant_id
    # Best-effort lookup through tenant_domains via a lightweight query
    with engine.connect() as conn:
        row = conn.execute(text("""
            select td.tenant_id
            from tenant_domains td
            where lower(td.domain) = lower(:host)
            limit 1
        """), {"host": host}).first()
        if row and row[0]:
            return str(row[0])
    raise HTTPException(status_code=400, detail="Tenant not resolved")


def with_tenant_db(db: Session, tenant_id: str) -> Session:
    # Set the app.tenant_id setting for RLS and defaults
    db.execute(text("select set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})
    # Lightweight metering increment per request path
    try:
        from datetime import datetime
        period = datetime.utcnow().strftime("%Y-%m")
        db.execute(
            text(
                """
                insert into metering_counters (id, tenant_id, metric, period, value)
                values (gen_random_uuid(), :tid, 'api_calls', :p, 1)
                on conflict (tenant_id, metric, period) do update set value = metering_counters.value + 1
                """
            ),
            {"tid": tenant_id, "p": period},
        )
        db.commit()
    except Exception:
        pass
    return db

