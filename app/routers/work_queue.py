from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.core.deps import get_db, get_claims
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
    type: str


@router.get("/work-queue", response_model=List[WorkItem])
def work_queue(db: Session = Depends(get_db), x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"), x_role: Optional[str] = Header(default=None, alias="X-Role"), claims: dict = Depends(get_claims)):
    if not x_org_id:
        raise HTTPException(400, "X-Org-Id required")
    if x_role == "SalesAgent":
        return []
    q = db.query(Task)
    tenant_id = claims.get("tenant_id")
    if tenant_id and hasattr(Task, 'tenant_id'):
        q = q.filter(Task.tenant_id == tenant_id)
    assigned_steps = (
        db.query(Assignment.step_type)
        .filter(Assignment.org_id == x_org_id)
        .distinct()
        .all()
    )
    steps = [s[0] for s in assigned_steps]
    if steps:
        q = q.filter(Task.step.in_(steps))
    task_rows = q.order_by(Task.sla_due_at.is_(None), Task.sla_due_at.asc()).all()

    # Incidents for the org (assigned_org_id = x_org_id), ordered by due_at
    iq = db.query(Incident).filter(Incident.assigned_org_id == x_org_id)
    if tenant_id and hasattr(Incident, 'tenant_id'):
        iq = iq.filter(Incident.tenant_id == tenant_id)
    inc_rows = iq.order_by(Incident.due_at.is_(None), Incident.due_at.asc()).all()

    items: list[WorkItem] = []
    for t in task_rows:
        items.append(WorkItem(
            id=str(t.id),
            pon_id=str(t.pon_id) if t.pon_id else None,
            step=t.step,
            status=t.status,
            sla_due_at=t.sla_due_at.isoformat() if t.sla_due_at else None,
            type="task",
        ))
    for inc in inc_rows:
        items.append(WorkItem(
            id=str(inc.id),
            pon_id=str(inc.pon_id) if getattr(inc, 'pon_id', None) else None,
            step=inc.category,
            status=inc.status,
            sla_due_at=inc.due_at.isoformat() if getattr(inc, 'due_at', None) else None,
            type="incident",
        ))
    return items

