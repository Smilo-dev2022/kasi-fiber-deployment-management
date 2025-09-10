from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.models.pon import PON
from app.models.task import Task
from app.models.cac import CACCheck
from app.models.smme import SMME
from sqlalchemy import func


router = APIRouter(prefix="/reports", tags=["reports"])


class WeeklyIn(BaseModel):
    start: date | None = None
    end: date | None = None


@router.post("/weekly", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def weekly(payload: WeeklyIn, db: Session = Depends(get_db)):
    start = payload.start or (date.today() - timedelta(days=7))
    end = payload.end or date.today()
    total = db.query(func.count(PON.id)).scalar() or 0
    completed = db.query(func.count(PON.id)).filter(PON.status == "Completed").scalar() or 0
    breaches = db.query(func.count(Task.id)).filter(Task.breached == True).scalar() or 0
    first_pass = db.query(func.count(CACCheck.id)).filter(CACCheck.passed == True).scalar() or 0
    smme_count = db.query(func.count(SMME.id)).scalar() or 0
    # placeholder pdf url
    url = f"https://example.local/reports/{uuid4()}.pdf"
    # Use database-specific UUID function if present; fall back to passing URL only and generating id client-side when needed
    try:
        db.execute(
            "insert into reports (id, kind, period_start, period_end, url) values (gen_random_uuid(), 'WeeklyExec', :s, :e, :u)",
            {"s": start, "e": end, "u": url},
        )
    except Exception:
        db.execute(
            "insert into reports (id, kind, period_start, period_end, url) values (:id, 'WeeklyExec', :s, :e, :u)",
            {"id": str(uuid4()), "s": start, "e": end, "u": url},
        )
    db.commit()
    return {
        "period_start": str(start),
        "period_end": str(end),
        "kpis": {
            "pons_total": total,
            "pons_completed": completed,
            "sla_breaches": breaches,
            "cac_first_pass": first_pass,
            "smmes": smme_count,
        },
        "url": url,
    }
