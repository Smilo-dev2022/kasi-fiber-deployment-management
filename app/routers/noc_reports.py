from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/noc", tags=["noc"])


@router.get("/uptime_by_ward", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def uptime_by_ward(days: int = 7, db: Session = Depends(get_db)):
    # Approximation using incidents DeviceDown
    q = text(
        """
        with window as (
            select ward,
                   sum(case when status='Resolved' then coalesce(ttr_seconds,0) else 0 end) as total_downtime
            from incidents
            where category='DeviceDown' and opened_at >= now() - (:days || ' days')::interval
            group by ward
        )
        select ward, greatest(0, 1.0 - (total_downtime / (86400*:days))) as uptime_ratio
        from window
        """
    )
    rows = db.execute(q, {"days": days}).mappings().all()
    return {"items": rows}


@router.get("/mttr_mttd", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def mttr_mttd(days: int = 30, db: Session = Depends(get_db)):
    q = text(
        """
        select avg(ttd_seconds) as mttd, avg(ttr_seconds) as mttr
        from incidents
        where opened_at >= now() - (:days || ' days')::interval and status='Resolved'
        """
    )
    row = db.execute(q, {"days": days}).mappings().first() or {"mttd": None, "mttr": None}
    return row


@router.get("/top_flapping_onus", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def top_flapping_onus(limit: int = 20, db: Session = Depends(get_db)):
    q = text(
        """
        select o.serial, o.name, o.flap_count, d.hostname, p.name as port
        from onus o
        join devices d on d.id = o.device_id
        left join ports p on p.id = o.port_id
        order by o.flap_count desc nulls last
        limit :limit
        """
    )
    rows = db.execute(q, {"limit": limit}).mappings().all()
    return {"items": rows}


@router.get("/optical_drift", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def optical_drift(days: int = 7, db: Session = Depends(get_db)):
    # Drift = last reading - baseline
    q = text(
        """
        with last_read as (
            select onu_id, max(taken_ts) as last_ts
            from optical_readings
            group by onu_id
        ),
        readings as (
            select r.onu_id, r.value_dbm
            from optical_readings r
            join last_read lr on lr.onu_id = r.onu_id and lr.last_ts = r.taken_ts
        )
        select o.serial, b.baseline_dbm, r.value_dbm, (r.value_dbm - b.baseline_dbm) as drift
        from optical_baselines b
        join onus o on o.id = b.onu_id
        left join readings r on r.onu_id = b.onu_id
        order by abs(r.value_dbm - b.baseline_dbm) desc nulls last
        limit 100
        """
    )
    rows = db.execute(q).mappings().all()
    return {"items": rows}

