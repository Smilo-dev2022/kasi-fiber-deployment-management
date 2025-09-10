from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.core.deps import get_db, require_roles, get_claims
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentOut
from app.models.orgs import Contract, Assignment
from app.services.audit import write_audit


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentOut])
def list_incidents(db: Session = Depends(get_db), status: Optional[str] = Query(None), device_id: Optional[str] = Query(None), claims: dict = Depends(get_claims)):
    q = db.query(Incident)
    tenant_id = claims.get("tenant_id")
    if tenant_id:
        q = q.filter(Incident.tenant_id == tenant_id)
    if status:
        q = q.filter(Incident.status == status)
    if device_id:
        q = q.filter(Incident.device_id == UUID(device_id))
    return q.order_by(Incident.opened_at.desc()).all()


@router.post("", response_model=IncidentOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db), claims: dict = Depends(get_claims)):
    inc = Incident(**payload.dict())
    if claims.get("tenant_id"):
        inc.tenant_id = claims["tenant_id"]
    # Auto-route assignment by PON/ward and scope
    scope = payload.category if payload.category in ("Power", "Optical", "Device", "Link") else "Technical"
    # Map categories to scope types
    scope_map = {"Power": "Maintenance", "Optical": "Technical", "Device": "Technical", "Link": "Technical"}
    scope_type = scope_map.get(payload.category, "Maintenance")
    assigned = (
        db.query(Assignment)
        .filter(Assignment.step_type == scope_type)
        .filter((Assignment.pon_id == payload.pon_id) | (Assignment.pon_id.is_(None)))
        .first()
    )
    if assigned:
        inc.assigned_org_id = assigned.org_id
        # SLA by contract
        con = (
            db.query(Contract)
            .filter(Contract.org_id == assigned.org_id)
            .filter(Contract.scope_type == scope_type)
            .filter((Contract.active.is_(True)))
            .first()
        )
        if con:
            sev_map = {"P1": con.sla_p1_min, "P2": con.sla_p2_min, "P3": con.sla_p3_min, "P4": con.sla_p4_min}
            mins = sev_map.get(payload.severity or "P3")
            if mins:
                inc.severity_sla_minutes = mins
                inc.due_at = datetime.now(timezone.utc) + timedelta(minutes=mins)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


@router.patch("/{incident_id}", response_model=IncidentOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_incident(incident_id: str, payload: IncidentUpdate, db: Session = Depends(get_db), claims: dict = Depends(get_claims)):
    inc = db.get(Incident, UUID(incident_id))
    if not inc:
        raise HTTPException(404, "Not found")
    tenant_id = claims.get("tenant_id")
    if tenant_id and str(inc.tenant_id) != tenant_id:
        raise HTTPException(403, "Forbidden")
    before = {k: getattr(inc, k, None) for k in ("status", "assigned_org_id", "severity_sla_minutes", "due_at", "ack_at")}
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(inc, k, v)
    if inc.status == "Acknowledged" and not inc.ack_at:
        inc.ack_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inc)
    after = {k: getattr(inc, k, None) for k in ("status", "assigned_org_id", "severity_sla_minutes", "due_at", "ack_at")}
    write_audit(db, entity_type="incident", entity_id=inc.id, action="update", by=str(claims.get("sub","")), before=before, after=after)
    db.commit()
    return inc


class AssignIn(IncidentUpdate):
    pass


@router.patch("/assign", response_model=IncidentOut, dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def assign_incident(id: str = Query(...), org_id: Optional[str] = Query(None), db: Session = Depends(get_db), claims: dict = Depends(get_claims)):
    inc = db.get(Incident, UUID(id))
    if not inc:
        raise HTTPException(404, "Not found")
    tenant_id = claims.get("tenant_id")
    if tenant_id and str(inc.tenant_id) != tenant_id:
        raise HTTPException(403, "Forbidden")
    if org_id:
        inc.assigned_org_id = UUID(org_id)
        # recompute due_at based on severity and contract
        con = (
            db.query(Contract)
            .filter(Contract.org_id == inc.assigned_org_id)
            .filter(Contract.active.is_(True))
            .first()
        )
        if con:
            sev_map = {"P1": con.sla_p1_min, "P2": con.sla_p2_min, "P3": con.sla_p3_min, "P4": con.sla_p4_min}
            mins = sev_map.get(inc.severity or "P3")
            if mins:
                inc.severity_sla_minutes = mins
                if not inc.opened_at:
                    inc.opened_at = datetime.now(timezone.utc)
                inc.due_at = inc.opened_at + timedelta(minutes=mins)
    db.commit()
    db.refresh(inc)
    return inc

