from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractIn(BaseModel):
    org_id: str
    scope: str = Field(pattern="^(Civil|Technical|Maintenance|Sales)$")
    wards: Optional[List[str]] = None
    sla_minutes_p1: int = 120
    sla_minutes_p2: int = 240
    sla_minutes_p3: int = 1440
    sla_minutes_p4: int = 4320
    rate_card_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    active: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_contract(payload: ContractIn, db: Session = Depends(get_db)):
    cid = str(uuid4())
    db.execute(
        text(
            """
      insert into contracts (id, org_id, scope, wards, sla_minutes_p1, sla_minutes_p2, sla_minutes_p3, sla_minutes_p4,
                             rate_card_id, start_date, end_date, active)
      values (:id, :o, :s, :w, :p1, :p2, :p3, :p4, :rc, :sd, :ed, :ac)
    """
        ),
        {
            "id": cid,
            "o": payload.org_id,
            "s": payload.scope,
            "w": payload.wards,
            "p1": payload.sla_minutes_p1,
            "p2": payload.sla_minutes_p2,
            "p3": payload.sla_minutes_p3,
            "p4": payload.sla_minutes_p4,
            "rc": payload.rate_card_id,
            "sd": payload.start_date,
            "ed": payload.end_date,
            "ac": payload.active,
        },
    )
    db.commit()
    return {"ok": True, "id": cid}

