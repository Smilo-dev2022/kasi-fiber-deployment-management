from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

from app.core.deps import get_db, require_roles
from app.core.settings import get_settings


router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentResolveIn(BaseModel):
    root_cause: str
    fix_code: str
    resolution_notes: Optional[str] = None
    photo_id: Optional[str] = None
    optical_dbm: Optional[float] = None


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def list_open(db: Session = Depends(get_db)):
    rows = db.execute(text("select * from incidents where status='Open' order by opened_at desc limit 500")).mappings().all()
    return {"items": rows}


@router.post("/{incident_id}/ack", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def acknowledge(incident_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text("update incidents set acknowledged_at=now(), ttd_seconds=extract(epoch from (now()-opened_at)) where id=:id and acknowledged_at is null returning 1"),
        {"id": incident_id},
    ).first()
    db.commit()
    return {"ok": bool(row)}


@router.post("/{incident_id}/resolve", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def resolve(incident_id: str, payload: IncidentResolveIn, db: Session = Depends(get_db)):
    # Enforce guards
    inc = db.execute(text("select requires_photo, requires_optical from incidents where id=:id"), {"id": incident_id}).mappings().first()
    if not inc:
        raise HTTPException(404, "Not found")
    if inc["requires_photo"] and not payload.photo_id:
        raise HTTPException(400, "Photo required")
    if inc["requires_optical"] and payload.optical_dbm is None:
        raise HTTPException(400, "Optical reading required")

    row = db.execute(
        text(
            """
            update incidents
            set status='Resolved', resolved_at=now(),
                ttr_seconds=extract(epoch from (now()-opened_at)),
                root_cause=:rc, fix_code=:fc, resolution_notes=:notes
            where id=:id
            returning sla_due_at
            """
        ),
        {"id": incident_id, "rc": payload.root_cause, "fc": payload.fix_code, "notes": payload.resolution_notes},
    ).first()
    db.commit()
    return {"ok": True}


@router.post("/create", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def create_manual(db: Session = Depends(get_db)):
    # sample incidents for testing
    db.execute(
        text(
            """
            insert into incidents (id, tenant_id, category, severity, status, dedup_key, description)
            values 
            (gen_random_uuid(), 'default', 'DeviceDown', 'P1', 'Open', 'sample|dev', 'Sample device down'),
            (gen_random_uuid(), 'default', 'OpticalLow', 'P2', 'Open', 'sample|opt', 'Sample optical low')
            """
        )
    )
    db.commit()
    return {"ok": True}

