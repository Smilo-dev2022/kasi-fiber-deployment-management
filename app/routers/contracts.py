from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID as UUID_t
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractIn(BaseModel):
    org_id: UUID_t
    scope: str
    wards: Optional[List[UUID_t]] = None
    sla_minutes_p1: int | None = None
    sla_minutes_p2: int | None = None
    sla_minutes_p3: int | None = None
    sla_minutes_p4: int | None = None
    rate_card: Optional[dict] = None
    active: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_contract(payload: ContractIn, db: Session = Depends(get_db)):
    db.execute(
        """
        insert into contracts (id, org_id, scope, wards, sla_minutes_p1, sla_minutes_p2, sla_minutes_p3, sla_minutes_p4, rate_card, active, created_at)
        values (gen_random_uuid(), :org, :scope, :wards, coalesce(:p1, 60), coalesce(:p2, 240), coalesce(:p3, 1440), coalesce(:p4, 4320), :rc, :act, now())
        """,
        {
            "org": str(payload.org_id),
            "scope": payload.scope,
            "wards": [str(w) for w in (payload.wards or [])],
            "p1": payload.sla_minutes_p1,
            "p2": payload.sla_minutes_p2,
            "p3": payload.sla_minutes_p3,
            "p4": payload.sla_minutes_p4,
            "rc": payload.rate_card,
            "act": payload.active,
        },
    )
    db.commit()
    return {"ok": True}

