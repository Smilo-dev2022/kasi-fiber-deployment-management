import os
import logging
import os as _os
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import tasks as tasks_router
from app.routers import certificate_acceptance as certacc_router
from app.routers import pons_geofence as pons_geo_router
from app.routers import photos_validate as photos_val_router
from app.routers import assets as assets_router
from app.routers import reports as reports_router
from app.routers import rate_cards as rate_router
from app.routers import pay_sheets as pays_router
from app.routers import contracts as contracts_router
from app.routers import assignments as assignments_router
from app.routers import photos_upload_hook as photos_upload_router
from app.routers import devices as devices_router
from app.routers import incidents as incidents_router
from app.routers import optical as optical_router
from app.routers import nms_webhook as nms_router
from app.routers import closures as closures_router
from app.routers import trays as trays_router
from app.routers import splices as splices_router
from app.routers import tests_plans as plans_router
from app.routers import tests_otdr as otdr_router
from app.routers import tests_lspm as lspm_router
from app.routers import work_queue as workq_router
from app.routers import topology as topo_router
from app.routers import maintenance as maint_router
from app.routers import configs as configs_router
from app.routers import spares as spares_router
from app.scheduler import init_jobs
from app.routers import reports as reports_router
from app.routers import invoices as invoices_router
from app.routers import metrics as metrics_router
from app.routers.security_upload_middleware import enforce_upload_limits


logging.basicConfig(level=_os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI()

# Sentry initialization (optional)
try:
    import sentry_sdk

    if _os.getenv("SENTRY_DSN"):
        sentry_sdk.init(dsn=_os.getenv("SENTRY_DSN"), environment=_os.getenv("ENVIRONMENT", "local"))
except Exception:
    pass

# CORS allowlist
origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware and basic context logging
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id") or str(uuid4())
    request.state.request_id = req_id
    response = None
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.exception("Unhandled error for request_id=%s", req_id)
        return JSONResponse(status_code=500, content={"error": "internal_error", "request_id": req_id})
    if response is not None:
        response.headers["X-Request-Id"] = req_id
    return response


@app.middleware("http")
async def uploads_guard(request: Request, call_next):
    return await enforce_upload_limits(request, call_next)

app.include_router(tasks_router.router)
app.include_router(certacc_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(metrics_router.router)
app.include_router(invoices_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)
app.include_router(contracts_router.router)
app.include_router(assignments_router.router)
app.include_router(photos_upload_router.router)
app.include_router(devices_router.router)
app.include_router(incidents_router.router)
app.include_router(optical_router.router)
app.include_router(closures_router.router)
app.include_router(trays_router.router)
app.include_router(splices_router.router)
app.include_router(plans_router.router)
app.include_router(otdr_router.router)
app.include_router(lspm_router.router)
app.include_router(nms_router.router)
app.include_router(workq_router.router)
app.include_router(topo_router.router)
app.include_router(maint_router.router)
app.include_router(configs_router.router)
app.include_router(spares_router.router)

init_jobs()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    # Real dependency checks: DB, Redis, S3
    from sqlalchemy import text
    from app.core.deps import SessionLocal
    from app.services import s3 as s3_service

    # DB check
    try:
        with SessionLocal() as db:
            db.execute(text("select 1"))
    except Exception as e:
        return {"ready": False, "dependency": "db", "error": str(e)}, 503

    # Redis check
    try:
        import os as _os
        import redis as _redis

        redis_url = _os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = _redis.from_url(redis_url)
        if r.ping() is not True:
            raise RuntimeError("redis ping failed")
    except Exception as e:
        return {"ready": False, "dependency": "redis", "error": str(e)}, 503

    # S3 check
    try:
        s3 = s3_service.get_client()
        bucket = s3_service.settings.S3_BUCKET
        s3.list_objects_v2(Bucket=bucket, Prefix="test", MaxKeys=1)
    except Exception as e:
        return {"ready": False, "dependency": "s3", "error": str(e)}, 503

    return {"ready": True}

