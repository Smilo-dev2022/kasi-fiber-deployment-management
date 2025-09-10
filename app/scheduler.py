from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from sqlalchemy import text

from app.core.deps import SessionLocal


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
        # Page P1 incidents that are overdue
        db.execute(
            text(
                """
            update pons set sla_breaches = sla_breaches + 1
            where id in (
              select pon_id from incidents where due_at is not null and status <> 'Closed' and due_at < :now and severity = 'P1'
            )
        """
            ),
            {"now": now},
        )
        db.commit()


def job_photo_revalidate():
    with SessionLocal() as db:
        db.execute(text("""
            update photos set exif_ok = exif_ok where taken_ts is not null
        """))
        db.commit()


def job_weekly_report():
    with SessionLocal() as db:
        db.execute(text("select 1"))


def init_jobs():
    sched.add_job(job_sla_scan, "interval", minutes=15, id="sla-scan")
    sched.add_job(job_photo_revalidate, "cron", hour=18, minute=0, id="photo-revalidate")
    sched.add_job(job_weekly_report, "cron", day_of_week="mon", hour=6, minute=0, id="weekly-report")
    sched.start()

