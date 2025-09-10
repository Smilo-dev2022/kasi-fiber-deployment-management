from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional, List
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.orgs import Assignment
from sqlalchemy import text


router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskUpdateIn(BaseModel):
    status: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


DEFAULT_SLA = {
    "Permissions": 72 * 60,
    "PolePlanting": 48 * 60,
    "CAC": 24 * 60,
    "Stringing": 48 * 60,
    "Invoicing": 24 * 60,
}


@router.patch("/{task_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_task(task_id: str, payload: TaskUpdateIn, db: Session = Depends(get_db)):
    from uuid import UUID

    task = db.get(Task, UUID(task_id))
    if not task:
        raise HTTPException(404, "Not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)
    if "status" in data and data["status"] == "In Progress":
        mins = task.sla_minutes or DEFAULT_SLA.get(task.step, 24 * 60)
        task.sla_minutes = mins
        if task.started_at:
            task.sla_due_at = task.started_at + timedelta(minutes=mins)
    if "status" in data and data["status"] == "Done":
        # Guard: require required tags + EXIF + geofence when marking Done
        req = db.execute(
            text("select name from photo_tags where required_for_step=:st"),
            {"st": task.step},
        ).scalars().all()
        if req:
            ok = db.execute(
                text(
                    """
          select count(1) from photos ph
          join photo_tag_links l on l.photo_id=ph.id
          join photo_tags t on t.id=l.tag_id
          where ph.pon_id=:p and t.name = any(:req) and ph.exif_ok=true and ph.within_geofence=true
        """
                ),
                {"p": str(task.pon_id), "req": req},
            ).scalar_one()
            if ok < len(req):
                raise HTTPException(status_code=400, detail="Required photo tags missing or invalid")
        if task.sla_due_at and task.completed_at:
            task.breached = task.completed_at > task.sla_due_at
        task.breached = task.completed_at > task.sla_due_at
    db.commit()
    return {"ok": True, "breached": task.breached, "sla_due_at": task.sla_due_at}


class WorkItem(BaseModel):
    id: str
    pon_id: Optional[str]
    step: Optional[str]
    status: Optional[str]
    sla_due_at: Optional[str]


@router.get("/work-queue", response_model=List[WorkItem])
def work_queue(db: Session = Depends(get_db), x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"), x_role: Optional[str] = Header(default=None, alias="X-Role")):
    if not x_org_id:
        raise HTTPException(400, "X-Org-Id required")
    # Filter tasks by assignments for the org
    q = db.query(Task)
    # If role is SalesAgent, return empty (isolation)
    if x_role == "SalesAgent":
        return []
    # Join by PON assignment if any
    # Simplified: tasks where there exists assignment matching pon_id and step
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

