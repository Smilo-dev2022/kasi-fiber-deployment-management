from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel
from datetime import date
from uuid import uuid4, UUID
from app.core.deps import get_db, require_roles
from app.services.pdf import render_pay_sheet_pdf
from app.services.s3 import put_bytes


router = APIRouter(prefix="/pay-sheets", tags=["pay-sheets"])


class GenIn(BaseModel):
    smme_id: str
    period_start: date
    period_end: date


@router.post("/generate", dependencies=[Depends(require_roles("ADMIN","PM"))])
def generate(payload: GenIn, db: Session = Depends(get_db)):
    # Aggregate by step using rate_cards
    sql = text("""
    with
    pole_done as (
      select t.pon_id, t.smmme_id as smme_id, count(*)::numeric as qty, 'PolePlanting'::text as step
      from tasks t
      where t.step='PolePlanting' and t.status='Done' and date(t.completed_at) between :s and :e
      group by t.pon_id, t.smmme_id
    ),
    str_run as (
      select sr.pon_id, sr.completed_by as smme_user, coalesce(sum(sr.meters),0)::numeric as qty, 'Stringing'::text as step
      from stringing_runs sr
      where date(sr.completed_at) between :s and :e
      group by sr.pon_id, sr.completed_by
    ),
    cac_pass as (
      select c.pon_id, u.id as smme_id, count(*)::numeric as qty, 'CAC'::text as step
      from cac_checks c
      join users u on u.id = c.checked_by
      where c.passed = true and date(c.checked_at) between :s and :e
      group by c.pon_id, u.id
    ),
    unioned as (
      select pon_id, smme_id, step, qty from pole_done where smme_id = :sm
      union all
      select pon_id, smme_user::uuid as smme_id, step, qty from str_run where smme_user = :sm
      union all
      select pon_id, smme_id, step, qty from cac_pass where smme_id = :sm
    ),
    priced as (
      select u.pon_id, u.step, u.qty,
             rc.rate_cents,
             (u.qty * rc.rate_cents)::bigint as amount_cents
      from unioned u
      join rate_cards rc on rc.smme_id = u.smme_id and rc.step = u.step and rc.active = true
    )
    select pon_id::text as pon, step, qty::text, rate_cents, amount_cents
    from priced
    """)
    rows = db.execute(sql, {"s": payload.period_start, "e": payload.period_end, "sm": payload.smme_id}).mappings().all()

    if not rows:
        # create empty Draft sheet
        ps_id = str(uuid4())
        db.execute(text("""
            insert into pay_sheets (id, smme_id, period_start, period_end, total_cents, status)
            values (:id, :s, :ps, :pe, 0, 'Draft')
        """), {"id": ps_id, "s": payload.smme_id, "ps": payload.period_start, "pe": payload.period_end})
        db.commit()
        return {"ok": True, "pay_sheet_id": ps_id, "lines": 0}

    total = sum(r["amount_cents"] for r in rows)
    ps_id = str(uuid4())
    db.execute(text("""
        insert into pay_sheets (id, smme_id, period_start, period_end, total_cents, status)
        values (:id, :s, :ps, :pe, :tot, 'Draft')
    """), {"id": ps_id, "s": payload.smme_id, "ps": payload.period_start, "pe": payload.period_end, "tot": total})
    for r in rows:
        db.execute(text("""
            insert into pay_sheet_lines (id, pay_sheet_id, pon_id, step, quantity, rate_cents, amount_cents)
            values (gen_random_uuid(), :ps, :pon::uuid, :st, :q::numeric, :rate, :amt)
        """), {"ps": ps_id, "pon": r["pon"], "st": r["step"], "q": r["qty"], "rate": r["rate_cents"], "amt": r["amount_cents"]})
    db.commit()
    return {"ok": True, "pay_sheet_id": ps_id, "total_cents": total, "lines": len(rows)}


@router.get("/{pay_sheet_id}/pdf", dependencies=[Depends(require_roles("ADMIN","PM"))])
def export_pdf(pay_sheet_id: str, db: Session = Depends(get_db)):
    # Fetch header
    hdr = db.execute(text("""
      select ps.id, ps.period_start, ps.period_end, ps.total_cents, ps.status,
             s.name as smme_name
      from pay_sheets ps
      join smmes s on s.id = ps.smme_id
      where ps.id = :id
    """), {"id": pay_sheet_id}).mappings().first()
    if not hdr:
        raise HTTPException(404, "Not found")
    lines = db.execute(text("""
      select l.pon_id::text as pon, l.step, l.quantity as qty, l.rate_cents, l.amount_cents
      from pay_sheet_lines l
      where l.pay_sheet_id = :id
      order by l.pon_id, l.step
    """), {"id": pay_sheet_id}).mappings().all()
    header = {
        "SMME": hdr["smme_name"],
        "Period": f'{hdr["period_start"]} to {hdr["period_end"]}',
        "Status": hdr["status"],
        "Total (ZAR)": f'R {hdr["total_cents"]/100:,.2f}',
    }
    pdf = render_pay_sheet_pdf(header, lines)
    key = f"reports/pay-sheets/{pay_sheet_id}.pdf"
    url = put_bytes(key, "application/pdf", pdf)
    db.execute(text("update pay_sheets set url=:u where id=:id"), {"u": url, "id": pay_sheet_id})
    db.commit()
    return {"ok": True, "url": url}

