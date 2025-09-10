from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.models.smme import SMME
from sqlalchemy import text


router = APIRouter(prefix="/pay-sheets", tags=["pay-sheets"])


class GenIn(BaseModel):
    smme_id: str
    period_start: date
    period_end: date


@router.post("/generate", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def generate(payload: GenIn, db: Session = Depends(get_db)):
    # Aggregate by PON and step with active rates
    # Poles
    poles_q = text(
        """
        insert into pay_sheet_lines (id, pay_sheet_id, pon_id, step, quantity, rate_cents, amount_cents)
        select gen_random_uuid(), :ps_id, t.pon_id, 'PolePlanting',
               count(*)::numeric as qty,
               rc.rate_cents,
               (count(*)::bigint * rc.rate_cents) as amt
        from tasks t
        join rate_cards rc on rc.smme_id = t.smmme_id and rc.step='PolePlanting' and rc.active
        where t.step='PolePlanting' and t.status='Done' and t.completed_at::date between :s and :e and t.smmme_id = :smme
        group by t.pon_id, rc.rate_cents
        """
    )
    # Stringing placeholder: assume tasks table has meters in sla_minutes temporarily is not correct; skip unless stringing_runs exists
    ps_id = str(uuid4())
    db.execute(
        text(
            """insert into pay_sheets (id, smme_id, period_start, period_end, total_cents, status)
                values (:id, :s, :ps, :pe, 0, 'Draft')"""
        ),
        {"id": ps_id, "s": payload.smme_id, "ps": payload.period_start, "pe": payload.period_end},
    )
    db.execute(poles_q, {"ps_id": ps_id, "s": payload.period_start, "e": payload.period_end, "smme": payload.smme_id})
    # Recompute total
    db.execute(
        text(
            "update pay_sheets set total_cents = coalesce((select sum(amount_cents) from pay_sheet_lines where pay_sheet_id=:id),0) where id=:id"
        ),
        {"id": ps_id},
    )
    db.commit()
    return {"ok": True, "pay_sheet_id": ps_id}


class StatusIn(BaseModel):
    status: str


@router.patch("/{pay_sheet_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def set_status(pay_sheet_id: str, payload: StatusIn, db: Session = Depends(get_db)):
    # Guards: only allow Draft -> Submitted -> Approved
    cur = db.execute(text("select status from pay_sheets where id=:id"), {"id": pay_sheet_id}).first()
    if not cur:
        raise HTTPException(404, "Not found")
    current = cur[0]
    target = payload.status
    allowed = {
        "Draft": {"Submitted"},
        "Submitted": {"Approved", "Draft"},
        "Approved": set(),
    }
    if target not in allowed.get(current, set()):
        raise HTTPException(400, "Invalid status transition")
    # Lock lines when Submitted
    if target == "Submitted":
        db.execute(text("update pay_sheet_lines set rate_cents = rate_cents where pay_sheet_id=:id"), {"id": pay_sheet_id})
    db.execute(text("update pay_sheets set status=:st where id=:id"), {"st": target, "id": pay_sheet_id})
    db.commit()
    return {"ok": True}

