from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.pon import PON
from app.services.routing import route_task


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
    # Auto-assign to contractor based on step and PON
    if task.pon_id:
        pon = db.get(PON, task.pon_id)
        if pon:
            route_task(db, task, pon)
    if "status" in data and data["status"] == "In Progress":
        mins = task.sla_minutes or DEFAULT_SLA.get(task.step, 24 * 60)
        task.sla_minutes = mins
        if task.started_at:
            task.sla_due_at = task.started_at + timedelta(minutes=mins)
    if "status" in data and data["status"] == "Done" and task.sla_due_at and task.completed_at:
        task.breached = task.completed_at > task.sla_due_at
    db.commit()
    return {"ok": True, "breached": task.breached, "sla_due_at": task.sla_due_at}

