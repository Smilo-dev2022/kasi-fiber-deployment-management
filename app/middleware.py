import hashlib
import hmac
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.deps import SessionLocal


class TenantScopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        org_id = request.headers.get("X-Org-ID")
        # Set PostgreSQL settings for RLS policies in this connection
        db: Optional[Session] = None
        try:
            db = SessionLocal()
            if tenant_id:
                db.execute("select set_config('app.tenant_id', :v, true)", {"v": tenant_id})
            if org_id:
                db.execute("select set_config('app.org_id', :v, true)", {"v": org_id})
            db.commit()
        finally:
            if db is not None:
                db.close()
        response = await call_next(request)
        return response

