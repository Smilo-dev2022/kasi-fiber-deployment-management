from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.core.deps import get_db, require_roles
from app.models.incident import Incident
from app.models.optical import OpticalReading
from sqlalchemy import case


router = APIRouter(prefix="/ops", tags=["ops-reports"])


@router.get("/kpis", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def kpis(days: int = 7, db: Session = Depends(get_db)):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    total = db.query(func.count(Incident.id)).filter(Incident.opened_at >= start).scalar()
    resolved = db.query(func.count(Incident.id)).filter(Incident.opened_at >= start, Incident.resolved_at.isnot(None)).scalar()
    # MTTR in minutes for resolved incidents
    mttr = db.query(func.avg(func.extract("epoch", Incident.resolved_at) - func.extract("epoch", Incident.opened_at))).filter(
        Incident.opened_at >= start, Incident.resolved_at.isnot(None)
    ).scalar()
    mttr_min = round((mttr or 0) / 60.0, 1)

    # Uptime approximation: assume incidents represent downtime for affected components; uptime% = 1 - (downtime / total_time)
    # Here we compute across all P1/P2 incidents
    p1p2 = db.query(Incident).filter(Incident.opened_at >= start, Incident.severity.in_(["P1", "P2"]))
    downtime_sec = 0.0
    for inc in p1p2:
        end_ts = inc.resolved_at or end
        downtime_sec += (end_ts - inc.opened_at).total_seconds()
    total_time_sec = days * 24 * 3600.0
    uptime_pct = round(max(0.0, 1.0 - downtime_sec / total_time_sec) * 100.0, 3)

    repeat_faults = db.query(Incident.title, func.count(Incident.id)).filter(Incident.opened_at >= start).group_by(Incident.title).having(func.count(Incident.id) > 1).order_by(func.count(Incident.id).desc()).limit(10).all()

    # Optical drift count (>=3 dB change) per PON, quick approximation using min/max
    drift_rows = (
        db.query(
            OpticalReading.pon_id,
            OpticalReading.port_name,
            (func.max(OpticalReading.dBm) - func.min(OpticalReading.dBm)).label("span")
        )
        .filter(OpticalReading.taken_at >= start)
        .group_by(OpticalReading.pon_id, OpticalReading.port_name)
        .having((func.max(OpticalReading.dBm) - func.min(OpticalReading.dBm)) >= 3.0)
        .limit(200)
        .all()
    )
    optical_drift = len(drift_rows)

    return {
        "period_start": start,
        "period_end": end,
        "incidents": total,
        "resolved": resolved,
        "mttr_min": mttr_min,
        "uptime_pct": uptime_pct,
        "repeat_faults": [[t, int(c)] for t, c in repeat_faults],
        "optical_drift_ports": optical_drift,
    }

