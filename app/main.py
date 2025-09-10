from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_tenant_id_from_request, with_tenant_db

from app.routers import tasks as tasks_router
from app.routers import cac as cac_router
from app.routers import pons_geofence as pons_geo_router
from app.routers import photos_validate as photos_val_router
from app.routers import assets as assets_router
from app.routers import reports as reports_router
from app.routers import rate_cards as rate_router
from app.routers import pay_sheets as pays_router
from app.routers import tenants as tenants_router


app = FastAPI()

app.include_router(tasks_router.router)
app.include_router(cac_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)
app.include_router(tenants_router.router)


@app.middleware("http")
async def tenant_ctx_middleware(request: Request, call_next):
    # Resolve tenant and set RLS setting per-request
    try:
        # We open a lightweight connection to set the tenant for any ORM sessions created later
        # Each endpoint should still call with_tenant_db on the session
        tenant_id = None
        x_tid = request.headers.get("X-Tenant-Id")
        if x_tid:
            tenant_id = x_tid
        else:
            # Fallback: domain mapping via deps helper (uses engine)
            from app.core.deps import get_tenant_id_from_request as _resolve
            tenant_id = _resolve(request)
        request.state.tenant_id = tenant_id
    except Exception:
        request.state.tenant_id = None
    response = await call_next(request)
    return response

