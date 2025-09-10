from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.core.deps import get_db, require_roles
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentOut
from sqlalchemy import text


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentOut])
def list_incidents(db: Session = Depends(get_db), status: Optional[str] = Query(None), device_id: Optional[str] = Query(None)):
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status)
    if device_id:
        q = q.filter(Incident.device_id == UUID(device_id))
    return q.order_by(Incident.opened_at.desc()).all()


@router.post("", response_model=IncidentOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    inc = Incident(**payload.dict())
    # Auto route based on assignments and simple category->scope mapping
    scope = None
    if payload.category in ("Power",):
        scope = "Maintenance"
    elif payload.category in ("Optical", "Link"):
        scope = "Technical"
    elif payload.category in ("Device", "Capacity"):
        scope = "NOC"
    if scope and payload.pon_id:
        row = (
            db.execute(
                text(
                    """
                    select a.org_id from assignments a
                    join pons p on p.id = a.pon_id or p.ward_id = a.ward_id
                    where a.active = true and a.scope = :s and (a.pon_id = :pid or a.ward_id = p.ward_id)
                    limit 1
                    """
                ),
                {"s": scope, "pid": str(payload.pon_id)},
            )
            .mappings()
            .first()
        )
        if row:
            inc.assigned_org_id = row["org_id"]
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


@router.patch("/{incident_id}", response_model=IncidentOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_incident(incident_id: str, payload: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.get(Incident, UUID(incident_id))
    if not inc:
        raise HTTPException(404, "Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(inc, k, v)
    if inc.status == "Acknowledged" and not inc.ack_at:
        inc.ack_at = datetime.now(timezone.utc)
    if inc.severity and not inc.severity_sla_minutes:
        mins_map = {"P1": 60, "P2": 240, "P3": 1440, "P4": 4320}
        inc.severity_sla_minutes = mins_map.get(inc.severity, 1440)
    if inc.severity_sla_minutes and inc.opened_at and not inc.due_at:
        inc.due_at = inc.opened_at + timedelta(minutes=inc.severity_sla_minutes)
    db.commit()
    db.refresh(inc)
    return inc


@router.patch("/assign", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def assign_incident(incident_id: str = Query(...), org_id: str = Query(...), db: Session = Depends(get_db)):
    inc = db.get(Incident, UUID(incident_id))
    if not inc:
        raise HTTPException(404, "Not found")
    inc.assigned_org_id = UUID(org_id)
    db.commit()
    db.execute(
        text(
            """
            insert into incident_audits (id, incident_id, action, actor_org_id, metadata, at)
            values (gen_random_uuid(), :iid, 'assign', :actor, '{}', now())
            """
        ),
        {"iid": incident_id, "actor": org_id},
    )
    db.commit()
    return {"ok": True}

