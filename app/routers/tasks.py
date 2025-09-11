from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional, List
from app.core.deps import get_db, require_roles
from app.models.task import Task
from app.models.orgs import Assignment
from app.routers.tests_plans import _pon_gated


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
def update_task(task_id: str, payload: TaskUpdateIn, db: Session = Depends(get_db), request: Request = None):
    from uuid import UUID

    task = db.get(Task, UUID(task_id))
    if not task:
        raise HTTPException(404, "Not found")
    # Prevent marking Done unless a valid geotagged photo exists in the last 24h for the PON
    data = payload.dict(exclude_unset=True)
    if data.get("status") == "Done" and task.pon_id is not None:
        from datetime import datetime, timezone, timedelta
        from app.models.photo import Photo
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        ok = (
            db.query(Photo)
            .filter(Photo.pon_id == task.pon_id)
            .filter(Photo.exif_ok.is_(True))
            .filter(Photo.within_geofence.is_(True))
            .filter((Photo.taken_ts.is_(None)) | (Photo.taken_ts >= cutoff))
            .first()
            is not None
        )
        if not ok:
            raise HTTPException(400, "Valid geotagged photo within 24h required to complete task")
        # If this is an Invoicing step, ensure test gates pass for the PON
        if task.step == "Invoicing":
            if not _pon_gated(db, str(task.pon_id)):
                raise HTTPException(400, "OTDR/LSPM tests not passed for this PON; cannot complete invoicing")
    for k, v in data.items():
        setattr(task, k, v)
    if "status" in data and data["status"] == "In Progress":
        mins = task.sla_minutes or DEFAULT_SLA.get(task.step, 24 * 60)
        task.sla_minutes = mins
        if task.started_at:
            task.sla_due_at = task.started_at + timedelta(minutes=mins)
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


@router.get("/work-queue", response_model=List[WorkItem], dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "NOC"))])
def work_queue(request: "Request", db: Session = Depends(get_db)):
    # Filter tasks by assignments scoped to org from JWT
    from uuid import UUID
    q = db.query(Task)
    claims = getattr(request.state, "jwt_claims", {}) or {}
    role = claims.get("role")
    if role == "SalesAgent":
        return []
    org_id = getattr(request.state, "org_id", None)
    try:
        org_uuid = UUID(str(org_id)) if org_id else None
    except Exception:
        raise HTTPException(400, "Invalid org in token")
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

