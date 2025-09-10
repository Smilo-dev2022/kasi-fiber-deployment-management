from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.core.limiter import limiter, key_by_org
from app.models.orgs import Contract


router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractIn(BaseModel):
    org_id: str
    scope_type: str
    wards: Optional[List[str]] = None
    sla_p1_min: Optional[int] = None
    sla_p2_min: Optional[int] = None
    sla_p3_min: Optional[int] = None
    sla_p4_min: Optional[int] = None
    rate_card_ref: Optional[str] = None
    active: Optional[bool] = True
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


@router.post(
    "",
    dependencies=[Depends(require_roles("ADMIN", "PM")), Depends(limiter(20, 60, key_by_org))],
)
def create_contract(payload: ContractIn, db: Session = Depends(get_db)):
    data = payload.dict()
    data["id"] = uuid4()
    row = Contract(**data)
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}

