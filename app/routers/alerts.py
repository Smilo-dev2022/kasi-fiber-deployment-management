from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_scoped_db, require_roles
from sqlalchemy import text


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/dedupe")
def set_dedupe_window(device_id: str, category: str, minutes: int, db: Session = Depends(get_scoped_db)):
    # Simple implementation using a temp table of windows; create table if not exists
    db.execute(text(
        """
        create table if not exists alert_dedupe (
          device_id uuid,
          category text,
          window_min int,
          updated_at timestamptz default now(),
          primary key (device_id, category)
        )
        """
    ))
    db.execute(text("insert into alert_dedupe(device_id, category, window_min, updated_at) values (:d,:c,:m, now()) on conflict (device_id, category) do update set window_min = excluded.window_min, updated_at = now()"),
               {"d": device_id, "c": category, "m": minutes})
    db.commit()
    return {"ok": True}

