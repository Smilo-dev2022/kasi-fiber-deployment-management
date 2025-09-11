from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional, List
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.photo import Photo
from app.core.cache import cache_get, cache_set
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
    # Gate: block Done unless there is at least one validated photo for this PON within 24h
    if "status" in data and data["status"] == "Done":
        if not task.pon_id:
            raise HTTPException(400, "Task must be linked to a PON")
        # Check for validated photo: exif_ok and within_geofence true
        has_valid = (
            db.query(Photo)
            .filter(Photo.pon_id == task.pon_id)
            .filter(Photo.exif_ok == True)
            .filter(Photo.within_geofence == True)
            .first()
            is not None
        )
        if not has_valid:
            raise HTTPException(400, "Validated photo required (EXIF, GPS, time window)")
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


@router.get("/work-queue", response_model=List[WorkItem], dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME", "AUDITOR"))])
def work_queue(request: Request, db: Session = Depends(get_db)):
    org_id = getattr(request.state, "org_id", None)
    role = (getattr(request.state, "jwt_claims", {}) or {}).get("role")
    if not org_id:
        raise HTTPException(400, "Org not found in token")
    # Filter tasks by assignments for the org
    q = db.query(Task)
    # If role is SalesAgent, return empty (isolation)
    if role == "SalesAgent":
        return []
    # Join by PON assignment if any
    # Simplified: tasks where there exists assignment matching pon_id and step
    from uuid import UUID
    try:
        org_uuid = UUID(str(org_id))
    except Exception:
        raise HTTPException(400, "Invalid org id")
    assigned_steps = (
        db.query(Assignment.step_type)
        .filter(Assignment.org_id == org_uuid)
        .distinct()
        .all()
    )
    steps = [s[0] for s in assigned_steps]
    if steps:
        q = q.filter(Task.step.in_(steps))
    cache_key = f"workq:{org_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    rows = q.order_by(Task.sla_due_at.is_(None), Task.sla_due_at.asc()).all()
    out = [
        WorkItem(
            id=str(t.id),
            pon_id=str(t.pon_id) if t.pon_id else None,
            step=t.step,
            status=t.status,
            sla_due_at=t.sla_due_at.isoformat() if t.sla_due_at else None,
        )
        for t in rows
    ]
    cache_set(cache_key, [w.dict() for w in out], ttl_seconds=5)
    return out

