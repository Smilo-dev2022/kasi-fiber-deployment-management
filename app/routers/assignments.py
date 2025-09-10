from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.models.orgs import Assignment
from app.core.limiter import limiter, key_by_org


router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentIn(BaseModel):
    org_id: str
    pon_id: Optional[str] = None
    ward: Optional[str] = None
    step_type: str


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM")), Depends(limiter(20, 60, key_by_org))])
def create_assignment(payload: AssignmentIn, db: Session = Depends(get_db)):
    if not payload.pon_id and not payload.ward:
        raise HTTPException(400, "Provide pon_id or ward")
    data = payload.dict()
    data["id"] = uuid4()
    row = Assignment(**data)
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}

