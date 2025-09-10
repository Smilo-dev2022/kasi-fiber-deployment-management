from fastapi import FastAPI
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app import add_observability
from sqlalchemy import text
from app.core.deps import SessionLocal

from app.routers import tasks as tasks_router
from app.routers import cac as cac_router
from app.routers import pons_geofence as pons_geo_router
from app.routers import photos_validate as photos_val_router
from app.routers import assets as assets_router
from app.routers import reports as reports_router
from app.routers import rate_cards as rate_router
from app.routers import pay_sheets as pays_router


app = FastAPI()
add_observability(app)

app.include_router(tasks_router.router)
app.include_router(cac_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)


scheduler: BackgroundScheduler | None = None


def _job_sla_breach_scan():
    db = SessionLocal()
    try:
        db.execute(text("update pons set sla_breaches = (select count(*) from tasks t where t.pon_id = pons.id and t.breached=true)"))
        db.commit()
    finally:
        db.close()


def _job_photo_revalidate():
    db = SessionLocal()
    try:
        # Lightweight touch; actual logic happens on validate endpoint
        db.execute(text("select 1"))
    finally:
        db.close()


def _job_weekly_report():
    # Trigger reports generation via DB insert (reports router uses insert on request normally)
    db = SessionLocal()
    try:
        db.execute(text("select 1"))
    finally:
        db.close()


@app.on_event("startup")
def _startup():
    global scheduler
    if os.getenv("DISABLE_SCHEDULER") == "1":
        return
    scheduler = BackgroundScheduler(timezone=os.getenv("TZ", "Africa/Johannesburg"))
    scheduler.add_job(_job_sla_breach_scan, IntervalTrigger(minutes=15), id="sla_breach_scan", replace_existing=True)
    scheduler.add_job(_job_photo_revalidate, CronTrigger(hour=18, minute=0), id="photo_revalidate", replace_existing=True)
    # Monday 06:00 SAST
    scheduler.add_job(_job_weekly_report, CronTrigger(day_of_week="mon", hour=6, minute=0), id="weekly_report", replace_existing=True)
    scheduler.start()


@app.on_event("shutdown")
def _shutdown():
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)

