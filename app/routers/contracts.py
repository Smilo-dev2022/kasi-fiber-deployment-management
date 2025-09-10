from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.schemas.contract import ContractCreate, ContractOut


router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", response_model=ContractOut, dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    cid = str(uuid4())
    wards_csv = ",".join(payload.wards) if payload.wards else None
    db.execute(
        text(
            """
        insert into contracts (id, org_id, scope, wards, sla_p1_minutes, sla_p2_minutes, sla_p3_minutes, sla_p4_minutes, rate_card_id, valid_from, valid_to)
        values (:id, :org, :scope, :wards, :p1, :p2, :p3, :p4, :rc, :vf, :vt)
        """
        ),
        {
            "id": cid,
            "org": str(payload.org_id),
            "scope": payload.scope,
            "wards": wards_csv,
            "p1": payload.sla_p1_minutes,
            "p2": payload.sla_p2_minutes,
            "p3": payload.sla_p3_minutes,
            "p4": payload.sla_p4_minutes,
            "rc": str(payload.rate_card_id) if payload.rate_card_id else None,
            "vf": payload.valid_from,
            "vt": payload.valid_to,
        },
    )
    db.commit()
    row = (
        db.execute(text("select * from contracts where id = :id"), {"id": cid}).mappings().first()
    )
    if not row:
        raise HTTPException(500, "Failed to create contract")
    # expand wards csv to list for response
    data = dict(row)
    data["wards"] = data["wards"].split(",") if data.get("wards") else None
    return data

