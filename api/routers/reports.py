from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.pon import PON
from ..models.cac import CACCheck
from ..models.stringing import StringingRun
from ..models.photo import Photo
from ..models.invoice import Invoice
from ..deps import get_current_user


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/daily-site")
def daily_site(db: Session = Depends(get_db), user=Depends(get_current_user)):
    since = datetime.utcnow() - timedelta(days=1)
    pons_touched = db.query(PON).filter(PON.created_at >= since).count()
    poles_planted = db.query(PON).filter(PON.created_at >= since).with_entities(PON.poles_planted).all()
    cac_passes = db.query(CACCheck).filter(CACCheck.checked_at >= since, CACCheck.passed == True).count()
    meters_strung = sum(r.meters for r in db.query(StringingRun).filter(StringingRun.completed_at >= since).all())
    photos_uploaded = db.query(Photo).filter(Photo.taken_at >= since).count()
    return {
        "pons_touched": pons_touched,
        "poles_planted": sum(p[0] for p in poles_planted) if poles_planted else 0,
        "cac_passes": cac_passes,
        "meters_strung": meters_strung,
        "photos_uploaded": photos_uploaded,
    }


@router.get("/invoice-register")
def invoice_register(db: Session = Depends(get_db), user=Depends(get_current_user)):
    totals = {"Draft": 0, "Submitted": 0, "Approved": 0, "Paid": 0}
    for status in totals.keys():
        totals[status] = sum(i.amount_cents for i in db.query(Invoice).filter(Invoice.status == status).all())
    return totals

