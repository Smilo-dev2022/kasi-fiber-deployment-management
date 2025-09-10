import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from app.core.deps import get_db, require_roles
from app.models.task import Task


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

# Allow env overrides, e.g., SLA_MINUTES_POLEPLANTING=2880
for _step in list(DEFAULT_SLA.keys()):
    env_key = f"SLA_MINUTES_{_step.upper()}"
    try:
        _val = os.getenv(env_key)
        if _val:
            DEFAULT_SLA[_step] = int(_val)
    except Exception:
        pass


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
    # Block invalid closure without photo evidence for key steps
    if "status" in data and data["status"] == "Done":
        # Evidence required for these steps
        required_steps = {"PolePlanting", "Stringing", "CAC"}
        if task.step in required_steps:
            from app.models.photo import Photo
            has_photo = (
                db.query(Photo)
                .filter(
                    Photo.pon_id == task.pon_id,
                    Photo.exif_ok == True,
                    Photo.within_geofence == True,
                )
                .first()
                is not None
            )
            if not has_photo:
                raise HTTPException(400, "Photo evidence (EXIF+geofence) required before closure")
        if task.sla_due_at and task.completed_at:
            task.breached = task.completed_at > task.sla_due_at
    db.commit()
    return {"ok": True, "breached": task.breached, "sla_due_at": task.sla_due_at}

