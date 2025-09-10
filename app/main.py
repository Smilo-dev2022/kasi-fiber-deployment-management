import logging
import os
import sys
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import tasks as tasks_router
from app.routers import cac as cac_router
from app.routers import pons_geofence as pons_geo_router
from app.routers import photos_validate as photos_val_router
from app.routers import assets as assets_router
from app.routers import reports as reports_router
from app.routers import rate_cards as rate_router
from app.routers import pay_sheets as pays_router
from app.routers import admin_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.jobs import scan_sla_breaches, revalidate_photos, generate_weekly_report


app = FastAPI(docs_url="/docs", openapi_url="/openapi.json")


# Structured JSON logging
def _setup_logging():
    handler = logging.StreamHandler(sys.stdout)

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            base = {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, "request_id"):
                base["request_id"] = getattr(record, "request_id")
            return __import__("json").dumps(base, ensure_ascii=False)

    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    # Avoid duplicate handlers in reload
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)


_setup_logging()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # attach to state for downstream usage
        request.state.request_id = request_id
        response: Response
        try:
            response = await call_next(request)
        finally:
            pass
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIdMiddleware)


# CORS allowlist from env
cors_origins = [o for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )


# Sentry integration (optional)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")))
        app.add_middleware(SentryAsgiMiddleware)
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).warning("Sentry init failed: %s", exc)

app.include_router(tasks_router.router)
app.include_router(cac_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)
app.include_router(admin_router)


# Scheduler setup
scheduler: AsyncIOScheduler | None = None


@app.on_event("startup")
async def _startup_scheduler():
    global scheduler
    scheduler = AsyncIOScheduler()
    # SLA breach scan every 15 minutes
    scheduler.add_job(scan_sla_breaches, IntervalTrigger(minutes=15), id="sla-scan")
    # Photo revalidation daily 18:00
    scheduler.add_job(revalidate_photos, CronTrigger(hour=18, minute=0), id="photo-reval")
    # Weekly report Monday 06:00 SAST (UTC+2). Use UTC 04:00
    scheduler.add_job(generate_weekly_report, CronTrigger(day_of_week="mon", hour=4, minute=0), id="weekly-report")
    scheduler.start()


@app.on_event("shutdown")
async def _shutdown_scheduler():
    if scheduler:
        scheduler.shutdown(wait=False)
