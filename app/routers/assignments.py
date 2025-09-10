from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentIn(BaseModel):
    org_id: str
    scope: str = Field(pattern="^(Civil|Technical|Maintenance|Sales)$")
    pon_id: Optional[str] = None
    ward: Optional[str] = None
    priority: int = 100
    active: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_assignment(payload: AssignmentIn, db: Session = Depends(get_db)):
    if not payload.pon_id and not payload.ward:
        raise HTTPException(400, "Provide pon_id or ward")
    aid = str(uuid4())
    db.execute(
        text(
            """
      insert into assignments (id, org_id, scope, pon_id, ward, priority, active)
      values (:id, :o, :s, :p, :w, :pr, :ac)
    """
        ),
        {
            "id": aid,
            "o": payload.org_id,
            "s": payload.scope,
            "p": payload.pon_id,
            "w": payload.ward,
            "pr": payload.priority,
            "ac": payload.active,
        },
    )
    db.commit()
    return {"ok": True, "id": aid}

