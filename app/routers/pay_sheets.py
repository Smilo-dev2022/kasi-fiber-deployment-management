from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.models.smme import SMME
from app.models.civils import TrenchSegment, DuctInstall, Reinstatement
from sqlalchemy import text


router = APIRouter(prefix="/pay-sheets", tags=["pay-sheets"])


class GenIn(BaseModel):
    smme_id: str
    period_start: date
    period_end: date


@router.post("/generate", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def generate(payload: GenIn, db: Session = Depends(get_db)):
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


class CivilsLinesIn(BaseModel):
    pon_id: str
    include_trenching: bool = True
    include_reinstatement: bool = True


@router.post("/{pay_sheet_id}/add-civils-lines", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_civils_lines(pay_sheet_id: str, payload: CivilsLinesIn, db: Session = Depends(get_db)):
    ps = db.execute(
        text("select id, smme_id, period_start, period_end, status from pay_sheets where id=:id"),
        {"id": pay_sheet_id},
    ).mappings().first()
    if not ps:
        raise HTTPException(404, "Pay sheet not found")
    if ps["status"] != "Draft":
        raise HTTPException(400, "Only Draft pay sheets can be modified")

    def get_rate(step: str, unit: str, for_date: date) -> int:
        row = db.execute(
            text(
                """
                select rate_cents
                from rate_cards
                where smme_id=:s and step=:st and unit=:u and active=true
                  and valid_from<=:d and (valid_to is null or valid_to>=:d)
                order by valid_from desc
                limit 1
                """
            ),
            {"s": ps["smme_id"], "st": step, "u": unit, "d": ps["period_end"]},
        ).first()
        if not row:
            raise HTTPException(400, f"No active rate for {step} {unit}")
        return int(row[0])

    inserts = []
    # Trenching lines: segments Reinstated within period, and all duct installs mandrel_passed
    if payload.include_trenching:
        segs = (
            db.query(TrenchSegment)
            .filter(TrenchSegment.pon_id == payload.pon_id)
            .filter(TrenchSegment.status == "Reinstated")
            .filter(TrenchSegment.completed_at >= ps["period_start"]) 
            .filter(TrenchSegment.completed_at <= ps["period_end"]) 
            .all()
        )
        if segs:
            rate = get_rate("Trenching", "per_meter", ps["period_end"])
            for seg in segs:
                installs = db.query(DuctInstall).filter(DuctInstall.segment_id == seg.id).all()
                if not installs or any(not di.mandrel_passed for di in installs):
                    continue
                qty = float(seg.length_m or 0)
                if qty <= 0:
                    continue
                amount = int(round(qty * rate))
                inserts.append(
                    {
                        "pay_sheet_id": pay_sheet_id,
                        "pon_id": str(seg.pon_id),
                        "step": "Trenching",
                        "quantity": qty,
                        "rate_cents": rate,
                        "amount_cents": amount,
                    }
                )

    # Reinstatement lines: reinstatement signed off within period
    if payload.include_reinstatement:
        reins = (
            db.query(Reinstatement)
            .join(TrenchSegment, TrenchSegment.id == Reinstatement.segment_id)
            .filter(TrenchSegment.pon_id == payload.pon_id)
            .filter(Reinstatement.signed_off_by.isnot(None))
            .filter(Reinstatement.signed_off_at >= ps["period_start"]) 
            .filter(Reinstatement.signed_off_at <= ps["period_end"]).all()
        )
        if reins:
            rate = get_rate("Reinstatement", "per_m2", ps["period_end"])
            for r in reins:
                qty = float(r.area_m2 or 0)
                if qty <= 0:
                    continue
                # find segment pon
                seg = db.get(TrenchSegment, r.segment_id)
                amount = int(round(qty * rate))
                inserts.append(
                    {
                        "pay_sheet_id": pay_sheet_id,
                        "pon_id": str(seg.pon_id),
                        "step": "Reinstatement",
                        "quantity": qty,
                        "rate_cents": rate,
                        "amount_cents": amount,
                    }
                )

    for row in inserts:
        db.execute(
            text(
                """
                insert into pay_sheet_lines (id, pay_sheet_id, pon_id, step, quantity, rate_cents, amount_cents)
                values (gen_random_uuid(), :ps, :pon, :st, :q, :r, :a)
                """
            ),
            {
                "ps": row["pay_sheet_id"],
                "pon": row["pon_id"],
                "st": row["step"],
                "q": row["quantity"],
                "r": row["rate_cents"],
                "a": row["amount_cents"],
            },
        )
    db.commit()
    return {"ok": True, "added": len(inserts)}

