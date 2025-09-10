from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel
from datetime import date
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/invoices", tags=["invoices"])


class GenIn(BaseModel):
    org_id: str
    period_start: date
    period_end: date


@router.post("/generate", dependencies=[Depends(require_roles("ADMIN", "PM", "FINANCE"))])
def generate(payload: GenIn, db: Session = Depends(get_db)):
    inv_id = str(uuid4())

    failed = db.execute(
        text(
            """
      select count(*) from certificate_acceptance ca
      join pons p on p.id=ca.pon_id
      where ca.passed=false and date(ca.checked_at) between :s and :e
    """
        ),
        {"s": payload.period_start, "e": payload.period_end},
    ).scalar_one()
    if failed and failed > 0:
        raise HTTPException(400, "Certificate of Acceptance failures exist in period")

    db.execute(
        text(
            """
      insert into invoices (id, org_id, period_start, period_end, status, total_cents)
      values (:id,:o,:s,:e,'Draft',0)
    """
        ),
        {"id": inv_id, "o": payload.org_id, "s": payload.period_start, "e": payload.period_end},
    )

    db.execute(
        text(
            """
      insert into invoice_lines (id, invoice_id, pon_id, item_type, qty, rate_cents, amount_cents, source_ref_id)
      select gen_random_uuid(), :inv, ca.pon_id, 'CA', count(*)::numeric, rc.rate_cents,
             (count(*)*rc.rate_cents)::bigint, ca.id
      from certificate_acceptance ca
      join assignments a on a.step_type='Technical' and (a.pon_id=ca.pon_id or a.ward=(select ward from pons where id=ca.pon_id))
      join contracts c on c.org_id=a.org_id and c.active=true
      join rate_cards rc on rc.smme_id = a.org_id and rc.step='CAC' and rc.active=true
      where ca.passed=true and date(ca.checked_at) between :s and :e and a.org_id=:o
      group by ca.pon_id, rc.rate_cents, ca.id
    """
        ),
        {"inv": inv_id, "s": payload.period_start, "e": payload.period_end, "o": payload.org_id},
    )

    db.execute(
        text(
            """
      insert into invoice_lines (id, invoice_id, pon_id, item_type, qty, rate_cents, amount_cents, source_ref_id)
      select gen_random_uuid(), :inv, sr.pon_id, 'Stringing', sum(sr.meters)::numeric, rc.rate_cents,
             (sum(sr.meters)*rc.rate_cents)::bigint, null
      from stringing_runs sr
      join assignments a on a.step_type='Technical' and (a.pon_id=sr.pon_id or a.ward=(select ward from pons where id=sr.pon_id))
      join rate_cards rc on rc.smme_id=a.org_id and rc.step='Stringing' and rc.active=true
      where sr.qc_passed=true and date(coalesce(sr.end_ts, sr.start_ts)) between :s and :e and a.org_id=:o
      group by sr.pon_id, rc.rate_cents
    """
        ),
        {"inv": inv_id, "s": payload.period_start, "e": payload.period_end, "o": payload.org_id},
    )

    db.execute(
        text(
            """
      update invoices set total_cents=(select coalesce(sum(amount_cents),0) from invoice_lines where invoice_id=:id) where id=:id
    """
        ),
        {"id": inv_id},
    )

    db.commit()
    return {"ok": True, "invoice_id": inv_id}


class StatusIn(BaseModel):
    status: str  # Draft, Submitted, Approved, Rejected, Paid


@router.patch("/{invoice_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "FINANCE"))])
def set_status(invoice_id: str, payload: StatusIn, db: Session = Depends(get_db)):
    if payload.status in ("Submitted", "Approved", "Paid"):
        pass
    db.execute(text("update invoices set status=:s where id=:id"), {"s": payload.status, "id": invoice_id})
    db.commit()
    return {"ok": True}

