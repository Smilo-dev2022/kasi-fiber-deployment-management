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
    "Floating": 24 * 60,
    "Splicing": 24 * 60,
    "Testing": 48 * 60,
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
    if "status" in data and data["status"] == "Done" and task.sla_due_at and task.completed_at:
        task.breached = task.completed_at > task.sla_due_at
    # Guards
    if "status" in data and data["status"] == "In Progress" and task.step == "Stringing":
        # Block start if any floating run failed
        row = db.execute(
            text("select count(1) from floating_runs fr where fr.pon_id=:pon and fr.passed=false"),
            {"pon": task.pon_id},
        ).first()
        if row and row[0] and int(row[0]) > 0:
            raise HTTPException(400, "Cannot start Stringing: Floating run failed")
    if "status" in data and data["status"] == "Done" and task.step == "Invoicing":
        # Block if required tests not passed
        row = db.execute(
            text(
                """
            select count(1)
            from test_plans tp
            left join (
                select test_plan_id, bool_or(passed) as lspm_ok from lspm_results group by test_plan_id
            ) l on l.test_plan_id = tp.id
            left join (
                select test_plan_id, bool_or(passed) as otdr_ok from otdr_results group by test_plan_id
            ) o on o.test_plan_id = tp.id
            where tp.pon_id = :pon and (
                (tp.lspm_required and coalesce(l.lspm_ok,false)=false) or
                (tp.otdr_required and coalesce(o.otdr_ok,false)=false)
            )
            """
            ),
            {"pon": task.pon_id},
        ).first()
        if row and row[0] and int(row[0]) > 0:
            raise HTTPException(400, "Cannot complete Invoicing: tests pending or failed")
    db.commit()
    return {"ok": True, "breached": task.breached, "sla_due_at": task.sla_due_at}

