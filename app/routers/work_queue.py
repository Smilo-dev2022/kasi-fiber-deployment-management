from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.orgs import Assignment
from app.models.incident import Incident


router = APIRouter(prefix="", tags=["work-queue"])


class WorkItem(BaseModel):
    id: str
    pon_id: Optional[str]
    step: Optional[str]
    status: Optional[str]
    sla_due_at: Optional[str]


@router.get("/work-queue", response_model=List[WorkItem], dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "NOC", "AUDITOR"))])
def work_queue(db: Session = Depends(get_db), x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"), x_role: Optional[str] = Header(default=None, alias="X-Role")):
    if not x_org_id:
        raise HTTPException(400, "X-Org-Id required")
    if x_role == "SalesAgent":
        return []
    q = db.query(Task)
    assigned_steps = (
        db.query(Assignment.step_type)
        .filter(Assignment.org_id == x_org_id)
        .distinct()
        .all()
    )
    steps = [s[0] for s in assigned_steps]
    if steps:
        q = q.filter(Task.step.in_(steps))
    rows = q.order_by(Task.sla_due_at.is_(None), Task.sla_due_at.asc()).all()
    items = [
        WorkItem(
            id=str(t.id),
            pon_id=str(t.pon_id) if t.pon_id else None,
            step=t.step,
            status=t.status,
            sla_due_at=t.sla_due_at.isoformat() if t.sla_due_at else None,
        )
        for t in rows
    ]
    # Incidents for the same org
    incs = (
        db.query(Incident)
        .filter(Incident.assigned_org_id == x_org_id)
        .filter(Incident.status != "Closed")
        .order_by(Incident.due_at.is_(None), Incident.due_at.asc())
        .all()
    )
    for i in incs:
        items.append(
            WorkItem(
                id=str(i.id),
                pon_id=str(i.pon_id) if i.pon_id else None,
                step="Incident",
                status=i.status,
                sla_due_at=i.due_at.isoformat() if i.due_at else None,
            )
        )
    return items

