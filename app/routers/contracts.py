from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.schemas.contract import ContractIn, AssignmentIn


router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PMO"))])
def create_contract(payload: ContractIn, db: Session = Depends(get_db)):
    cid = str(uuid4())
    db.execute(
        text(
            """
        insert into contracts (id, org_id, scope, sla_p1_minutes, sla_p2_minutes, sla_p3_minutes, sla_p4_minutes, valid_from, valid_to)
        values (:id, :org, :scope, :p1, :p2, :p3, :p4, :vf, :vt)
      """
        ),
        {
            "id": cid,
            "org": payload.org_id,
            "scope": payload.scope,
            "p1": payload.sla_p1_minutes,
            "p2": payload.sla_p2_minutes,
            "p3": payload.sla_p3_minutes,
            "p4": payload.sla_p4_minutes,
            "vf": payload.valid_from,
            "vt": payload.valid_to,
        },
    )
    db.commit()
    return {"ok": True, "id": cid}


assign_router = APIRouter(prefix="/assignments", tags=["assignments"])


@assign_router.post("", dependencies=[Depends(require_roles("ADMIN", "PMO"))])
def create_assignment(payload: AssignmentIn, db: Session = Depends(get_db)):
    if not payload.pon_id and not payload.ward_code:
        raise HTTPException(400, "Provide pon_id or ward_code")
    aid = str(uuid4())
    db.execute(
        text(
            """
        insert into assignments (id, org_id, step, pon_id, ward_code)
        values (:id, :org, :step, :pon, :ward)
      """
        ),
        {
            "id": aid,
            "org": payload.org_id,
            "step": payload.step,
            "pon": payload.pon_id,
            "ward": payload.ward_code,
        },
    )
    db.commit()
    return {"ok": True, "id": aid}

