from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.models.orgs import Assignment
from sqlalchemy import text


router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentIn(BaseModel):
    org_id: str
    pon_id: Optional[str] = None
    ward: Optional[str] = None
    step_type: str


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_assignment(payload: AssignmentIn, db: Session = Depends(get_db)):
    if not payload.pon_id and not payload.ward:
        raise HTTPException(400, "Provide pon_id or ward")
    # Guard: block assignment if SMME compliance expired
    comp = db.execute(
        text(
            """
        select count(1) as ok
        from smmes s
        where s.id = :org
          and exists (
            select 1 from compliance_docs d
            where d.smme_id = s.id and d.verified = true and (d.valid_to is null or d.valid_to >= current_date)
          )
        """
        ),
        {"org": payload.org_id},
    ).scalar()
    if not comp:
        raise HTTPException(400, "SMME compliance invalid or expired")
    data = payload.dict()
    data["id"] = uuid4()
    row = Assignment(**data)
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}

