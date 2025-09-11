from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/maint-windows", tags=["maintenance"])


class MaintIn(BaseModel):
    scope: str = Field(description="Device|PON|Org|Global")
    target_id: Optional[UUID] = None
    start_at: datetime
    end_at: datetime
    approved_by: Optional[str] = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def create_window(payload: MaintIn, db: Session = Depends(get_db)):
    if payload.end_at <= payload.start_at:
        raise HTTPException(400, "end_at must be after start_at")
    wid = str(uuid4())
    db.execute(
        text(
            """
            insert into maint_windows (id, scope, target_id, start_at, end_at, approved_by)
            values (:id, :scope, :target, :start, :end, :by)
            """
        ),
        {
            "id": wid,
            "scope": payload.scope,
            "target": str(payload.target_id) if payload.target_id else None,
            "start": payload.start_at,
            "end": payload.end_at,
            "by": payload.approved_by,
        },
    )
    db.commit()
    return {"ok": True, "id": wid}

