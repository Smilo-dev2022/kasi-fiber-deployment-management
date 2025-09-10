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
    # aggregate
    q = text(
        """
    with
    poles as (
      select t.smmme_id as smme_id, t.pon_id, count(*)::numeric as qty
      from tasks t
      where t.step='PolePlanting' and t.status='Done' and t.completed_at::date between :s and :e
      group by t.smmme_id, t.pon_id
    ),
    strg as (
      select sr.completed_by as smme_user, sr.pon_id, coalesce(sum(sr.meters),0)::numeric as meters
      from stringing_runs sr
      where sr.completed_at::date between :s and :e
      group by sr.completed_by, sr.pon_id
    )
    select 1
    """
    )
    # minimal implementation. you can replace with full queries
    ps_id = str(uuid4())
    db.execute(
        text(
            """insert into pay_sheets (id, smme_id, period_start, period_end, total_cents, status)
                values (:id, :s, :ps, :pe, 0, 'Draft')"""
        ),
        {"id": ps_id, "s": payload.smme_id, "ps": payload.period_start, "pe": payload.period_end},
    )
    db.commit()
    return {"ok": True, "pay_sheet_id": ps_id}


class StatusIn(BaseModel):
    status: str


@router.patch("/{pay_sheet_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def set_status(pay_sheet_id: str, payload: StatusIn, db: Session = Depends(get_db)):
    db.execute(text("update pay_sheets set status=:st where id=:id"), {"st": payload.status, "id": pay_sheet_id})
    db.commit()
    return {"ok": True}
