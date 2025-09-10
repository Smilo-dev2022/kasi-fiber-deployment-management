from fastapi import APIRouter, Depends, HTTPException, Header
import os
import json
try:
    import redis
except Exception:
    redis = None
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.core.deps import get_db
from app.models.task import Task
from app.models.orgs import Assignment


router = APIRouter(prefix="", tags=["work-queue"])


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
    if x_role == "SalesAgent":
        return []
    # Cache per org for 30 seconds
    cache_key = f"workq:{x_org_id}"
    if redis is not None:
        try:
            r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
            cached = r.get(cache_key)
            if cached:
                return [WorkItem(**item) for item in json.loads(cached)]
        except Exception:
            pass
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
    if redis is not None:
        try:
            r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
            r.setex(cache_key, 30, json.dumps([i.dict() for i in items]))
        except Exception:
            pass
    return items

