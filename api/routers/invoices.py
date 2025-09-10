from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.invoice import Invoice
from ..models.pon import PON
from ..models.photo import Photo
from ..models.task import Task
from ..schemas.invoice import InvoiceOut, InvoiceCreate, InvoiceUpdate
from ..deps import get_current_user, require_roles
from ..services.audit import audit


router = APIRouter(tags=["Invoices"])


@router.get("/invoices", response_model=List[InvoiceOut])
def list_invoices(status: Optional[str] = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    return q.order_by(Invoice.id.desc()).all()


@router.post("/pons/{pon_id}/invoices", response_model=InvoiceOut)
def create_invoice(pon_id: int, payload: InvoiceCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pon = db.get(PON, pon_id)
    if not pon:
        raise HTTPException(404, detail="PON not found")
    # Draft invoice allowed after CAC passed on all required poles and stringing photos exist.
    has_stringing_photos = db.query(Photo).filter(Photo.pon_id == pon_id, Photo.kind == "Stringing").first() is not None
    if not (pon.cac_passed and has_stringing_photos):
        raise HTTPException(400, detail="CAC must pass and Stringing photos required for draft")
    invoice = Invoice(pon_id=pon_id, smme_id=pon.smme_id, amount_cents=payload.amount_cents, status="Draft")
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    audit(db, "Invoice", invoice.id, "CREATE", user.id, None, {"status": invoice.status})
    db.commit()
    return invoice


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, detail="Invoice not found")
    if payload.status == "Submitted":
        # Submit requires Dig, Plant, CAC, Stringing photos present and tasks marked Done
        required_kinds = {"Dig", "Plant", "CAC", "Stringing"}
        kinds = {k for (k,) in db.query(Photo.kind).filter(Photo.pon_id == inv.pon_id).distinct()}
        if not required_kinds.issubset(kinds):
            raise HTTPException(400, detail="Missing required photos for submit")
        steps_required = {"PolePlanting", "CAC", "Stringing"}
        done_steps = {t.step for t in db.query(Task).filter(Task.pon_id == inv.pon_id, Task.status == "Done").all()}
        if not steps_required.issubset(done_steps):
            raise HTTPException(400, detail="Required tasks not done")
        inv.status = "Submitted"
        inv.submitted_at = datetime.utcnow()
    elif payload.status == "Approved":
        # Approve restricted to ADMIN or PM
        require_roles("ADMIN", "PM")(user)  # will raise if not allowed
        inv.status = "Approved"
        inv.approved_by = user.id
    elif payload.status == "Paid":
        # Normally set via finance webhook
        inv.status = "Paid"
        inv.paid_at = datetime.utcnow()
    db.add(inv)
    db.commit()
    db.refresh(inv)
    audit(db, "Invoice", inv.id, "UPDATE", user.id, None, {"status": inv.status})
    db.commit()
    return inv

