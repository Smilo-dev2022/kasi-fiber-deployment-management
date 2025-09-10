import os
import logging
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.deps import SessionLocal
from app.services import s3 as s3_service
import redis as _redis

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


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), environment=os.getenv("APP_ENV", "development"))

app = FastAPI()

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


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id") or os.getenv("HOSTNAME", "local") + ":" + str(os.getpid()) + ":" + str(id(request))
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = req_id
    return response

app.include_router(tasks_router.router)
app.include_router(certacc_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
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
    # Check DB
    try:
        with SessionLocal() as db:
            db.execute(text("select 1"))
    except Exception as e:
        from fastapi import Response
        return Response(content='{"ready": false, "db": "down"}', media_type="application/json", status_code=503)

    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = _redis.Redis.from_url(redis_url)
        r.ping()
    except Exception as e:
        from fastapi import Response
        return Response(content='{"ready": false, "redis": "down"}', media_type="application/json", status_code=503)

    # Check S3
    try:
        s3 = s3_service.get_client()
        s3.list_objects_v2(Bucket=s3_service.settings.S3_BUCKET, Prefix="test", MaxKeys=1)
    except Exception as e:
        from fastapi import Response
        return Response(content='{"ready": false, "s3": "down"}', media_type="application/json", status_code=503)

    return {"ready": True}


@app.get("/metrics")
def metrics():
    # Lightweight counters; for more use Prometheus client
    try:
        with SessionLocal() as db:
            inc_created = db.execute(text("select count(1) from incidents")).scalar()
            inc_resolved = db.execute(text("select count(1) from incidents where status in ('Resolved','Closed')")).scalar()
            inc_breached = db.execute(text("select count(1) from tasks where breached = true")).scalar()
            return {
                "incidents": {"created": inc_created, "resolved": inc_resolved, "breached": inc_breached}
            }
    except Exception as e:
        return {"error": str(e)}

