from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.orgs import Assignment


router = APIRouter(prefix="", tags=["work-queue"])


class WorkItem(BaseModel):
    id: str
    pon_id: Optional[str]
    step: Optional[str]
    status: Optional[str]
    sla_due_at: Optional[str]


@router.get("/work-queue", response_model=List[WorkItem], dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME", "AUDITOR"))])
def work_queue(request: Request, db: Session = Depends(get_db)):
    org_id = getattr(request.state, "org_id", None)
    role = (getattr(request.state, "jwt_claims", {}) or {}).get("role")
    if not org_id:
        raise HTTPException(400, "Org not found in token")
    if role == "SalesAgent":
        return []
    q = db.query(Task)
    assigned_steps = (
        db.query(Assignment.step_type)
        .filter(Assignment.org_id == org_id)
        .distinct()
        .all()
    )
    steps = [s[0] for s in assigned_steps]
    if steps:
        q = q.filter(Task.step.in_(steps))
    rows = q.order_by(Task.sla_due_at.is_(None), Task.sla_due_at.asc()).all()
    return [
        WorkItem(
            id=str(t.id),
            pon_id=str(t.pon_id) if t.pon_id else None,
            step=t.step,
            status=t.status,
            sla_due_at=t.sla_due_at.isoformat() if t.sla_due_at else None,
        )
        for t in rows
    ]

