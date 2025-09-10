import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import tempfile
import subprocess
from app.services.s3 import put_bytes
from sqlalchemy import text

from app.core.deps import SessionLocal


logger = logging.getLogger("scheduler")
sched = BackgroundScheduler(timezone="Africa/Johannesburg")


def job_sla_scan():
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        db.execute(
            text(
                """
            update tasks set breached = true
            where sla_due_at is not null and status <> 'Done' and breached = false and sla_due_at < :now
        """
            ),
            {"now": now},
        )
        db.commit()
        logger.info("SLA scan completed at %s", now.isoformat())


def job_photo_revalidate():
    with SessionLocal() as db:
        db.execute(text("""
            update photos set exif_ok = exif_ok where taken_ts is not null
        """))
        db.commit()
        logger.info("Photo revalidate done")


def job_weekly_report():
    with SessionLocal() as db:
        db.execute(text("select 1"))
        logger.info("Weekly report trigger noop")


def job_daily_backup():
    if os.getenv("ENABLE_BACKUPS", "true").lower() != "true":
        return
    pg_dump_bin = os.getenv("PG_DUMP_PATH", "pg_dump")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL missing; skip backup")
        return
    ymd = datetime.now(timezone.utc).strftime("%Y%m%d")
    key = f"backups/daily/{ymd}.sql"
    try:
        with tempfile.NamedTemporaryFile(suffix=".sql") as tmp:
            cmd = [pg_dump_bin, db_url, "-F", "p", "-f", tmp.name]
            subprocess.check_call(cmd)
            with open(tmp.name, "rb") as fh:
                data = fh.read()
            url = put_bytes(key, "application/sql", data)
            logger.info("Backup uploaded to %s", url)
            return url
    except Exception as exc:  # pragma: no cover
        logger.exception("Backup failed: %s", exc)
        return None


def init_jobs():
    minutes = int(os.getenv("SLA_SCAN_MINUTES", "15"))
    sched.add_job(job_sla_scan, "interval", minutes=minutes, id="sla-scan", replace_existing=True)
    sched.add_job(
        job_photo_revalidate, "cron", hour=int(os.getenv("PHOTO_REVALIDATE_HOUR", "18")), minute=0, id="photo-revalidate", replace_existing=True
    )
    sched.add_job(
        job_weekly_report,
        "cron",
        day_of_week=os.getenv("WEEKLY_REPORT_DOW", "mon"),
        hour=int(os.getenv("WEEKLY_REPORT_HOUR", "6")),
        minute=int(os.getenv("WEEKLY_REPORT_MINUTE", "0")),
        id="weekly-report",
        replace_existing=True,
    )
    # Daily backups at 02:10
    sched.add_job(
        job_daily_backup,
        "cron",
        hour=int(os.getenv("BACKUP_HOUR", "2")),
        minute=int(os.getenv("BACKUP_MINUTE", "10")),
        id="daily-backup",
        replace_existing=True,
    )
    sched.start()

