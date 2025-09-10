from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import uuid4

from app.routers import db_dep
from app.core.deps import require_roles
from app.models.tenant import Tenant, TenantDomain, TenantTheme


router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantCreateIn(BaseModel):
    name: str
    code: str
    plan: str = "Starter"
    primary_domain: Optional[str] = None
    theme: Optional[Dict] = None


@router.post("", dependencies=[Depends(require_roles("ADMIN"))])
def create_tenant(payload: TenantCreateIn, db: Session = Depends(db_dep)):
    t = Tenant(id=uuid4(), name=payload.name, code=payload.code, plan=payload.plan)
    db.add(t)
    if payload.primary_domain:
        d = TenantDomain(id=uuid4(), tenant_id=t.id, domain=payload.primary_domain, is_primary=True)
        db.add(d)
    th = TenantTheme(id=uuid4(), tenant_id=t.id, theme=payload.theme or {})
    db.add(th)
    db.commit()
    return {"ok": True, "tenant_id": str(t.id)}


class TenantDomainIn(BaseModel):
    domain: str
    is_primary: bool = False


@router.post("/{tenant_id}/domains", dependencies=[Depends(require_roles("ADMIN"))])
def add_domain(tenant_id: str, payload: TenantDomainIn, db: Session = Depends(db_dep)):
    d = TenantDomain(id=uuid4(), tenant_id=tenant_id, domain=payload.domain, is_primary=payload.is_primary)
    db.add(d)
    db.commit()
    return {"ok": True}


class ThemeUpdateIn(BaseModel):
    theme: Dict
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    pdf_footer: Optional[str] = None


@router.put("/{tenant_id}/theme", dependencies=[Depends(require_roles("ADMIN"))])
def update_theme(tenant_id: str, payload: ThemeUpdateIn, db: Session = Depends(db_dep)):
    from sqlalchemy import select
    th = db.execute(select(TenantTheme).where(TenantTheme.tenant_id == tenant_id)).scalars().first()
    if not th:
        raise HTTPException(404, "Theme not found")
    th.theme = payload.theme
    th.logo_url = payload.logo_url
    th.favicon_url = payload.favicon_url
    th.pdf_footer = payload.pdf_footer
    db.commit()
    return {"ok": True}

