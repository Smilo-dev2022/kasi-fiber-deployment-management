from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.task import Task
from ..models.pon import PON
from ..schemas.task import TaskOut, TaskCreate, TaskUpdate
from ..models.photo import Photo
from ..services.audit import audit
from ..deps import get_current_user


router = APIRouter(tags=["Tasks"])


@router.get("/pons/{pon_id}/tasks", response_model=List[TaskOut])
def list_tasks(pon_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Task).filter(Task.pon_id == pon_id).all()


@router.post("/pons/{pon_id}/tasks", response_model=TaskOut)
def create_task(pon_id: int, payload: TaskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if db.get(PON, pon_id) is None:
        raise HTTPException(404, detail="PON not found")
    task = Task(
        pon_id=pon_id,
        step=payload.step,
        assigned_to=payload.assigned_to,
        smme_id=payload.smme_id,
        notes=payload.notes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    audit(db, "Task", task.id, "CREATE", user.id, None, {"id": task.id, "step": task.step})
    db.commit()
    return task


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, detail="Task not found")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        if data["status"] == "In Progress" and task.started_at is None:
            task.started_at = datetime.utcnow()
        if data["status"] == "Done" and task.completed_at is None:
            # Enforce photo requirements for PolePhotos, CAC, Stringing
            required_photo_steps = {"PolePhotos": "Plant", "CAC": "CAC", "Stringing": "Stringing"}
            kind_needed = required_photo_steps.get(task.step)
            if kind_needed:
                has_photo = (
                    db.query(Photo)
                    .filter(Photo.pon_id == task.pon_id, Photo.kind == kind_needed)
                    .first()
                    is not None
                )
                if not has_photo:
                    raise HTTPException(400, detail=f"Photo of kind {kind_needed} required before completing {task.step}")
            task.completed_at = datetime.utcnow()
    for k, v in data.items():
        setattr(task, k, v)
    db.add(task)
    db.commit()
    db.refresh(task)
    audit(db, "Task", task.id, "UPDATE", user.id, None, {"status": task.status})
    db.commit()
    return task

