from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import date
from uuid import uuid4

from app.core.deps import get_db, require_roles
from app.services.pdf import render_pay_sheet_pdf
from app.services.s3 import put_bytes


router = APIRouter(prefix="/invoices", tags=["invoices"])


class GenIn(BaseModel):
    org_id: str
    period_start: date
    period_end: date


@router.post("/generate", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def generate(payload: GenIn, db: Session = Depends(get_db)):
    # Guards: block if any CAC failed or required photos/tests missing
    guard = db.execute(
        text(
            """
        with failed_cac as (
          select 1 from certificate_acceptance where passed = false
        ),
        missing_photos as (
          select 1 from photo p where not (p.exif_ok and p.within_geofence)
        )
        select (exists(select 1 from failed_cac) or exists(select 1 from missing_photos)) as blocked
        """
        )
    ).scalar()
    if guard:
        raise HTTPException(400, "Invoice generation blocked: failed CAC or invalid photos")

    # Build line items from rate cards similar to pay sheets
    sql = text(
        """
    with cac_pass as (
      select c.pon_id, count(*)::numeric as qty, 'CAC'::text as item_type
      from certificate_acceptance c
      where c.passed = true and date(c.checked_at) between :s and :e
      group by c.pon_id
    ),
    stringing as (
      select sr.pon_id, coalesce(sum(sr.meters),0)::numeric as qty, 'Stringing'::text as item_type
      from stringing_runs sr
      where date(coalesce(sr.end_ts, sr.start_ts)) between :s and :e and sr.qc_passed = true
      group by sr.pon_id
    ),
    unioned as (
      select * from cac_pass
      union all
      select * from stringing
    )
    select u.pon_id::text as pon_id, u.item_type, u.qty::text, rc.rate_cents, (u.qty * rc.rate_cents)::bigint as amount_cents
    from unioned u
    join rate_cards rc on rc.smme_id = :org and rc.step = u.item_type and rc.active = true
    """
    )
    rows = db.execute(sql, {"s": payload.period_start, "e": payload.period_end, "org": payload.org_id}).mappings().all()

    inv_id = str(uuid4())
    total = sum(r["amount_cents"] for r in rows) if rows else 0
    db.execute(
        text("insert into invoices (id, org_id, period_start, period_end, total_cents, status) values (:i, :o, :s, :e, :t, 'Draft')"),
        {"i": inv_id, "o": payload.org_id, "s": payload.period_start, "e": payload.period_end, "t": total},
    )
    for r in rows:
        db.execute(
            text(
                """
            insert into invoice_lines (id, invoice_id, pon_id, item_type, qty, rate_cents, amount_cents)
            values (gen_random_uuid(), :inv, :pon::uuid, :it, :q::numeric, :rate, :amt)
            """
            ),
            {
                "inv": inv_id,
                "pon": r["pon_id"],
                "it": r["item_type"],
                "q": r["qty"],
                "rate": r["rate_cents"],
                "amt": r["amount_cents"],
            },
        )
    db.commit()
    return {"ok": True, "invoice_id": inv_id, "total_cents": total, "lines": len(rows)}


@router.get("/{invoice_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    hdr = db.execute(text("select * from invoices where id=:id"), {"id": invoice_id}).mappings().first()
    if not hdr:
        raise HTTPException(404, "Not found")
    lines = db.execute(text("select * from invoice_lines where invoice_id=:id order by pon_id"), {"id": invoice_id}).mappings().all()
    return {"header": dict(hdr), "lines": [dict(l) for l in lines]}


class InvoicePatch(BaseModel):
    status: str


@router.patch("/{invoice_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def update_invoice(invoice_id: str, payload: InvoicePatch, db: Session = Depends(get_db)):
    # Guard: Lock lines after Submitted
    if payload.status == "Submitted":
        db.execute(text("update invoices set status='Submitted' where id=:id"), {"id": invoice_id})
    else:
        db.execute(text("update invoices set status=:s where id=:id"), {"s": payload.status, "id": invoice_id})
    db.commit()
    return {"ok": True}


@router.get("/{invoice_id}/pdf", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def invoice_pdf(invoice_id: str, db: Session = Depends(get_db)):
    hdr = db.execute(text("select * from invoices where id=:id"), {"id": invoice_id}).mappings().first()
    lines = db.execute(text("select pon_id::text as pon, item_type as step, qty::text as qty, rate_cents, amount_cents from invoice_lines where invoice_id=:id"), {"id": invoice_id}).mappings().all()
    if not hdr:
        raise HTTPException(404, "Not found")
    header = {
        "SMME": hdr.get("org_id"),
        "Period": f'{hdr.get("period_start")} to {hdr.get("period_end")}',
        "Status": hdr.get("status"),
        "Total (ZAR)": f'R {hdr.get("total_cents", 0) / 100:,.2f}',
    }
    pdf = render_pay_sheet_pdf(header, lines)
    key = f"reports/invoices/{invoice_id}.pdf"
    url = put_bytes(key, "application/pdf", pdf)
    return {"ok": True, "url": url}

