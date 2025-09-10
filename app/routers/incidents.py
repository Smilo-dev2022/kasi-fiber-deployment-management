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


class AssignIn(IncidentUpdate):
    incident_id: str
    assigned_org_id: Optional[str] = None


@router.patch("/assign", dependencies=[Depends(require_roles("ADMIN", "PMO", "NOC"))])
def assign_incident(payload: AssignIn, db: Session = Depends(get_db)):
    inc = db.get(Incident, UUID(payload.incident_id))
    if not inc:
        raise HTTPException(404, "Not found")
    data = payload.dict(exclude_unset=True)
    assigned = data.pop("assigned_org_id", None)
    for k, v in data.items():
        setattr(inc, k, v)
    if assigned:
        inc.assigned_org_id = UUID(assigned)
        # compute due_at from contracts SLA by severity if available
        sev = inc.severity or "P3"
        row = (
            db.execute(
                text(
                    """
            select coalesce(
              case when :sev = 'P1' then sla_p1_minutes
                   when :sev = 'P2' then sla_p2_minutes
                   when :sev = 'P3' then sla_p3_minutes
                   else sla_p4_minutes end, null) as mins
            from contracts
            where org_id = :org and (valid_to is null or valid_to >= current_date) and valid_from <= current_date
            order by valid_from desc
            limit 1
          """
                ),
                {"org": str(inc.assigned_org_id), "sev": sev},
            )
            .mappings()
            .first()
        )
        mins = row["mins"] if row else None
        if mins:
            inc.severity_sla_minutes = int(mins)
            base = inc.opened_at or datetime.now(timezone.utc)
            inc.due_at = base + timedelta(minutes=int(mins))
    db.commit()
    db.refresh(inc)
    return {"ok": True, "id": str(inc.id), "assigned_org_id": str(inc.assigned_org_id) if inc.assigned_org_id else None, "due_at": inc.due_at}

