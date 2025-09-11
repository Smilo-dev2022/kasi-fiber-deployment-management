from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional, List
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.photo import Photo
from uuid import UUID
from app.models.orgs import Assignment


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
    # Hard gate: require at least one validated photo within geofence for the task's PON before marking Done
    if "status" in data and data["status"] == "Done":
        has_valid_photo = (
            db.query(Photo)
            .filter(Photo.pon_id == task.pon_id)
            .filter(Photo.exif_ok.is_(True))
            .filter(Photo.within_geofence.is_(True))
            .first()
            is not None
        )
        if not has_valid_photo:
            raise HTTPException(400, "Photo with valid EXIF and within geofence required")
    if "status" in data and data["status"] == "Done" and task.sla_due_at and task.completed_at:
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
    from uuid import UUID
    try:
        org_uuid = UUID(str(x_org_id))
    except Exception:
        raise HTTPException(400, "Invalid X-Org-Id")
    assigned_steps = (
        db.query(Assignment.step_type)
        .filter(Assignment.org_id == org_uuid)
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

