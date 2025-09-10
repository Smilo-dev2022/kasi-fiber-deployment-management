from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.deps import get_db, require_roles
from app.models.pon import PON
from app.models.incident import Incident
from app.models.optical import OpticalReading


router = APIRouter(prefix="/pons", tags=["pons"])


@router.get("/{pon_id}/incidents", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def pon_incidents(pon_id: str, db: Session = Depends(get_db)):
    pon = db.get(PON, UUID(pon_id))
    if not pon:
        raise HTTPException(404, "Not found")
    rows = (
        db.query(Incident)
        .filter(Incident.pon_id == UUID(pon_id))
        .order_by(Incident.opened_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "severity": r.severity,
            "status": r.status,
            "title": r.title,
            "opened_at": r.opened_at,
            "resolved_at": r.resolved_at,
        }
        for r in rows
    ]


@router.get("/{pon_id}/optical", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def pon_optical(pon_id: str, limit: int = 200, db: Session = Depends(get_db)):
    rows = (
        db.query(OpticalReading)
        .filter(OpticalReading.pon_id == UUID(pon_id))
        .order_by(OpticalReading.taken_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "taken_at": r.taken_at,
            "port_name": r.port_name,
            "direction": r.direction,
            "dBm": float(r.dBm) if r.dBm is not None else None,
        }
        for r in rows
    ]

