from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from sqlalchemy import text
from os import getenv

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
    # Paging simulation: emit a log when P1 due within 15 minutes
    if getenv("ENABLE_PAGING", "1") == "1":
        def job_page_p1():
            with SessionLocal() as db:
                rows = (
                    db.execute(
                        text(
                            """
                    select id::text from incidents
                    where severity = 'P1' and status in ('Open','Acknowledged')
                      and due_at is not null and due_at < now() + interval '15 minutes'
                  """
                        )
                    )
                    .mappings()
                    .all()
                )
                if rows:
                    print(f"[PAGE] P1 incidents nearing SLA: {[r['id'] for r in rows]}")
        sched.add_job(job_page_p1, "interval", minutes=5, id="page-p1")
    sched.add_job(job_photo_revalidate, "cron", hour=18, minute=0, id="photo-revalidate")
    sched.add_job(job_weekly_report, "cron", day_of_week="mon", hour=6, minute=0, id="weekly-report")
    sched.start()

