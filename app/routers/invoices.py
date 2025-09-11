from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4, UUID
from app.core.deps import get_db, require_roles
from app.services.pdf import render_pay_sheet_pdf
from app.services.s3 import put_object_bytes


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def generate_invoice(pon_id: str, db: Session = Depends(get_db)):
    # Technical gates: verify test plans and passing OTDR/LSPM exist
    row = (
        db.execute(
            text(
                """
                select exists(select 1 from test_plans where pon_id = :p) as has_plan,
                       exists(select 1 from otdr_results r join test_plans tp on r.test_plan_id=tp.id where tp.pon_id=:p and r.passed) as otdr_ok,
                       exists(select 1 from lspm_results r join test_plans tp on r.test_plan_id=tp.id where tp.pon_id=:p and r.passed) as lspm_ok
                """
            ),
            {"p": pon_id},
        )
        .mappings()
        .first()
    )
    if not row or not row["has_plan"] or not row["otdr_ok"] or not row["lspm_ok"]:
        raise HTTPException(400, "Technical gates not satisfied (plan, OTDR pass, LSPM pass required)")

    inv_id = str(uuid4())
    # Minimal header/lines; real implementation should aggregate pay items per PON
    header = {"SMME": "Pilot SMME", "Period": "This Month", "Status": "Locked", "Total (ZAR)": "0.00"}
    lines: list[dict] = []
    pdf = render_pay_sheet_pdf(header, lines)
    key = f"reports/invoices/{inv_id}.pdf"
    url = put_object_bytes(key, pdf, content_type="application/pdf")
    db.execute(text("insert into invoices (id, pon_id, url, status) values (:id, :p, :u, 'Locked')"), {"id": inv_id, "p": str(UUID(pon_id)), "u": url})
    db.commit()
    return {"ok": True, "invoice_id": inv_id, "url": url}

