from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
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
    db.commit()
    db.refresh(inc)
    return inc


class IncidentAssignIn(IncidentUpdate):
    assigned_org_id: UUID
    notes: Optional[str] = None


@router.patch("/assign", response_model=IncidentOut, dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def assign_incident(incident_id: str = Query(...), payload: IncidentAssignIn = None, db: Session = Depends(get_db)):
    inc = db.get(Incident, UUID(incident_id))
    if not inc:
        raise HTTPException(404, "Not found")
    prev_org = inc.assigned_org_id
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(inc, k, v)
    # audit
    db.execute(
        text(
            """
        insert into incident_audits (id, incident_id, action, from_org_id, to_org_id, by_role, by_org_id, notes)
        values (gen_random_uuid(), :iid, 'assign', :from_org, :to_org, :role, :by_org, :notes)
        """
        ),
        {
            "iid": str(inc.id),
            "from_org": str(prev_org) if prev_org else None,
            "to_org": str(payload.assigned_org_id),
            "role": None,
            "by_org": None,
            "notes": payload.notes,
        },
    )
    db.commit()
    db.refresh(inc)
    return inc

