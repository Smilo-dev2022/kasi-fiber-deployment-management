from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/incidents", tags=["incidents"])


class AssignIn(BaseModel):
    org_id: str
    severity: str | None = None  # P1..P4 override optional


@router.post("/{incident_id}/assign", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def assign(incident_id: str, payload: AssignIn, db: Session = Depends(get_db)):
    # fetch contract SLA
    row = db.execute(
        text(
            """
      select sla_minutes_p1, sla_minutes_p2, sla_minutes_p3, sla_minutes_p4
      from contracts where active = true and org_id = :o
      order by created_at desc limit 1
    """
        ),
        {"o": payload.org_id},
    ).mappings().first()
    if not row:
        raise HTTPException(400, "Contract for org not found")

    sev = payload.severity or "P3"
    mins = {"P1": row["sla_minutes_p1"], "P2": row["sla_minutes_p2"], "P3": row["sla_minutes_p3"], "P4": row["sla_minutes_p4"]}[sev]

    db.execute(
        text(
            """
      update incidents
      set assigned_org_id = :o, severity_sla_minutes = :m, due_at = :d
      where id = :id
    """
        ),
        {"o": payload.org_id, "m": mins, "d": datetime.now(timezone.utc) + timedelta(minutes=mins), "id": incident_id},
    )
    db.commit()
    return {"ok": True}

