from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone, date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import SessionLocal


log = logging.getLogger(__name__)


def _with_session(func):
    def wrapper(*args: Any, **kwargs: Any):
        db: Session = SessionLocal()
        try:
            return func(db=db, *args, **kwargs)
        finally:
            db.close()

    return wrapper


@_with_session
def scan_sla_breaches(db: Session):
    # Mark tasks breached where due_at passed and not completed
    q = text(
        """
        update tasks
        set breached = true
        where breached = false
          and sla_due_at is not null
          and (completed_at is null or completed_at > sla_due_at)
          and now() at time zone 'utc' > sla_due_at
        """
    )
    db.execute(q)
    # Update PON sla_breaches count
    db.execute(
        text(
            """
            update pons p set sla_breaches = x.cnt
            from (
              select pon_id, count(*)::int as cnt from tasks where breached = true group by pon_id
            ) x
            where p.id = x.pon_id
            """
        )
    )
    db.commit()
    log.info("SLA breach scan completed")


@_with_session
def revalidate_photos(db: Session):
    # Recompute EXIF recency for last 2 days
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
    db.execute(
        text(
            """
            update photos
            set exif_ok = (coalesce(taken_ts, taken_at) is not null and (now() at time zone 'utc' - coalesce(taken_ts, taken_at)) <= interval '24 hours')
            where coalesce(taken_ts, taken_at) > :cutoff
            """
        ),
        {"cutoff": two_days_ago},
    )
    db.commit()
    log.info("Photo revalidation completed")


@_with_session
def generate_weekly_report(db: Session):
    # Call existing reports weekly endpoint's core logic via SQL insert
    today = date.today()
    start = today - timedelta(days=7)
    url = f"https://example.local/reports/{today.isoformat()}.pdf"
    db.execute(
        text(
            "insert into reports (id, kind, period_start, period_end, url) values (gen_random_uuid(), 'WeeklyExec', :s, :e, :u)"
        ),
        {"s": start, "e": today, "u": url},
    )
    db.commit()
    log.info("Weekly report generated", extra={"period_start": str(start), "period_end": str(today)})

