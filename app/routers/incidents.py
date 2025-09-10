from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.incident import Incident
from app.models.photo import Photo


router = APIRouter(prefix="/incidents", tags=["incidents"])


SLA_BY_SEVERITY = {
    "P1": {"response": 15, "restore": 120},
    "P2": {"response": 30, "restore": 240},
    "P3": {"response": 240, "restore": 24 * 60},
    "P4": {"response": 24 * 60, "restore": 3 * 24 * 60},
}


class IncidentIn(BaseModel):
    severity: str
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    device_id: Optional[str] = None
    pon_id: Optional[str] = None


@router.post("/", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_incident(payload: IncidentIn, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    targets = SLA_BY_SEVERITY.get(payload.severity, {"response": 60, "restore": 6 * 60})
    inc = Incident(
        id=uuid4(),
        severity=payload.severity,
        category=payload.category,
        status="Open",
        title=payload.title,
        description=payload.description,
        device_id=UUID(payload.device_id) if payload.device_id else None,
        pon_id=UUID(payload.pon_id) if payload.pon_id else None,
        opened_at=now,
        sla_response_min=targets["response"],
        sla_restore_min=targets["restore"],
    )
    db.add(inc)
    db.commit()
    return {"id": str(inc.id)}


@router.get("/", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def list_incidents(status: Optional[str] = None, severity: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status)
    if severity:
        q = q.filter(Incident.severity == severity)
    q = q.order_by(Incident.opened_at.desc()).limit(500)
    rows = q.all()
    return [
        {
            "id": str(r.id),
            "severity": r.severity,
            "category": r.category,
            "status": r.status,
            "title": r.title,
            "device_id": str(r.device_id) if r.device_id else None,
            "pon_id": str(r.pon_id) if r.pon_id else None,
            "opened_at": r.opened_at,
            "acknowledged_at": r.acknowledged_at,
            "resolved_at": r.resolved_at,
            "closed_at": r.closed_at,
        }
        for r in rows
    ]


class IncidentStatusIn(BaseModel):
    status: str
    root_cause: Optional[str] = None
    fix_code: Optional[str] = None
    close_notes: Optional[str] = None
    close_photo_id: Optional[str] = None


@router.patch("/{incident_id}/status", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_status(incident_id: str, payload: IncidentStatusIn, db: Session = Depends(get_db)):
    inc = db.get(Incident, UUID(incident_id))
    if not inc:
        raise HTTPException(404, "Not found")
    now = datetime.now(timezone.utc)
    old_status = inc.status
    inc.status = payload.status
    if payload.status == "Acknowledged" and not inc.acknowledged_at:
        inc.acknowledged_at = now
        if inc.sla_response_min:
            inc.breached_response = (inc.acknowledged_at - inc.opened_at) > timedelta(minutes=inc.sla_response_min)
    if payload.status == "Resolved" and not inc.resolved_at:
        inc.resolved_at = now
        if inc.sla_restore_min:
            inc.breached_restore = (inc.resolved_at - inc.opened_at) > timedelta(minutes=inc.sla_restore_min)
    if payload.status == "Closed":
        # Enforce closure requirements: root cause, fix code, and photo
        if not payload.root_cause or not payload.fix_code or not payload.close_photo_id:
            raise HTTPException(400, "root_cause, fix_code and close_photo_id are required to close")
        # Validate photo EXIF+GPS within geofence when linked to a PON
        try:
            photo = db.get(Photo, UUID(payload.close_photo_id))
        except Exception:
            photo = None
        if not photo:
            raise HTTPException(400, "close_photo_id not found")
        if inc.pon_id:
            from datetime import timedelta
            if not (photo.taken_ts and photo.exif_ok and photo.within_geofence and photo.pon_id == inc.pon_id and (now - photo.taken_ts) <= timedelta(hours=24)):
                raise HTTPException(400, "Close photo must have valid EXIF+GPS within PON geofence in last 24h")
        inc.root_cause = payload.root_cause
        inc.fix_code = payload.fix_code
        inc.close_notes = payload.close_notes
        inc.close_photo_id = UUID(payload.close_photo_id)
        if not inc.resolved_at:
            inc.resolved_at = now
        inc.closed_at = now
    db.commit()
    return {"ok": True, "old_status": old_status, "new_status": inc.status}

