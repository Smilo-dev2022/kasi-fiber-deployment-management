from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID as UUID_t
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentIn(BaseModel):
    org_id: UUID_t
    scope: str
    step_type: Optional[str] = None
    ward_id: Optional[UUID_t] = None
    pon_id: Optional[UUID_t] = None
    active: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_assignment(payload: AssignmentIn, db: Session = Depends(get_db)):
    db.execute(
        """
        insert into assignments (id, org_id, scope, step_type, ward_id, pon_id, active, created_at)
        values (gen_random_uuid(), :org, :scope, :step, :ward, :pon, :act, now())
        """,
        {
            "org": str(payload.org_id),
            "scope": payload.scope,
            "step": payload.step_type,
            "ward": str(payload.ward_id) if payload.ward_id else None,
            "pon": str(payload.pon_id) if payload.pon_id else None,
            "act": payload.active,
        },
    )
    db.commit()
    return {"ok": True}

