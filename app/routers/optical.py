from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4, UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db, require_roles
from app.models.optical import OpticalReading


router = APIRouter(prefix="/optical", tags=["optical"])


class OpticalIn(BaseModel):
    device_id: Optional[str] = None
    pon_id: Optional[str] = None
    onu_id: Optional[str] = None
    port_name: Optional[str] = None
    direction: Optional[str] = None
    dBm: Optional[float] = None
    taken_at: Optional[datetime] = None


@router.post("/ingest", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def ingest(payload: List[OpticalIn], db: Session = Depends(get_db)):
    count = 0
    for item in payload:
        rec = OpticalReading(
            id=uuid4(),
            device_id=UUID(item.device_id) if item.device_id else None,
            pon_id=UUID(item.pon_id) if item.pon_id else None,
            onu_id=UUID(item.onu_id) if item.onu_id else None,
            port_name=item.port_name,
            direction=item.direction,
            dBm=item.dBm,
            taken_at=item.taken_at or datetime.now(timezone.utc),
        )
        db.add(rec)
        count += 1
    db.commit()
    return {"ingested": count}


@router.get("/series", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def series(pon_id: Optional[str] = None, device_id: Optional[str] = None, port_name: Optional[str] = None, limit: int = 500, db: Session = Depends(get_db)):
    q = db.query(OpticalReading)
    if pon_id:
        q = q.filter(OpticalReading.pon_id == UUID(pon_id))
    if device_id:
        q = q.filter(OpticalReading.device_id == UUID(device_id))
    if port_name:
        q = q.filter(OpticalReading.port_name == port_name)
    q = q.order_by(OpticalReading.taken_at.desc()).limit(limit)
    rows = q.all()
    return [
        {
            "taken_at": r.taken_at,
            "dBm": float(r.dBm) if r.dBm is not None else None,
            "port_name": r.port_name,
            "direction": r.direction,
            "pon_id": str(r.pon_id) if r.pon_id else None,
            "device_id": str(r.device_id) if r.device_id else None,
            "onu_id": str(r.onu_id) if r.onu_id else None,
        }
        for r in rows
    ]


@router.get("/drift", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def drift(pon_id: str, hours: int = 24, db: Session = Depends(get_db)):
    # Returns ports whose mean changed by >= 3 dB in the period vs prior period
    # This uses two window buckets for simplicity
    from datetime import timedelta
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    prev_start = start - timedelta(hours=hours)

    # Current window
    cur = db.query(
        OpticalReading.port_name,
        func.avg(OpticalReading.dBm).label("avg_dbm"),
    ).filter(
        OpticalReading.pon_id == UUID(pon_id),
        OpticalReading.taken_at >= start,
        OpticalReading.taken_at < end,
    ).group_by(OpticalReading.port_name).all()

    prev = db.query(
        OpticalReading.port_name,
        func.avg(OpticalReading.dBm).label("avg_dbm"),
    ).filter(
        OpticalReading.pon_id == UUID(pon_id),
        OpticalReading.taken_at >= prev_start,
        OpticalReading.taken_at < start,
    ).group_by(OpticalReading.port_name).all()

    prev_map = {r[0]: float(r[1]) if r[1] is not None else None for r in prev}
    out = []
    for port, avg_dbm in cur:
        if avg_dbm is None:
            continue
        prev_avg = prev_map.get(port)
        if prev_avg is None:
            continue
        delta = float(avg_dbm) - float(prev_avg)
        if abs(delta) >= 3.0:
            out.append({"port_name": port, "delta_db": round(delta, 2), "avg_now": round(float(avg_dbm), 2), "avg_prev": round(prev_avg, 2)})
    return out

