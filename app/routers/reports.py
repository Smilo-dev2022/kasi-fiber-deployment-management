from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.core.limiter import env_org_limiter
from app.core.cache import cache_get, cache_set
from app.models.pon import PON
from app.models.task import Task
from app.models.certificate_acceptance import CertificateAcceptance
from app.models.smme import SMME
from sqlalchemy import func, text


router = APIRouter(prefix="/reports", tags=["reports"])


class WeeklyIn(BaseModel):
    start: date | None = None
    end: date | None = None


@router.post("/weekly", dependencies=[Depends(require_roles("ADMIN", "PM")), Depends(env_org_limiter("HEAVY_ORG", 60, 60))])
def weekly(payload: WeeklyIn, db: Session = Depends(get_db)):
    start = payload.start or (date.today() - timedelta(days=7))
    end = payload.end or date.today()
    cache_key = f"weekly:{start}:{end}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    total = db.query(func.count(PON.id)).scalar()
    completed = db.query(func.count(PON.id)).filter(PON.status == "Completed").scalar()
    breaches = db.query(func.count(Task.id)).filter(Task.breached == True).scalar()
    first_pass = db.query(func.count(CertificateAcceptance.id)).filter(CertificateAcceptance.passed == True).scalar()
    smme_count = db.query(func.count(SMME.id)).scalar()
    url = f"https://example.local/reports/{uuid4()}.pdf"
    db.execute(
        text(
            "insert into reports (id, kind, period_start, period_end, url) values (gen_random_uuid(), 'WeeklyExec', :s, :e, :u)"
        ),
        {"s": start, "e": end, "u": url},
    )
    db.commit()
    resp = {
        "period_start": str(start),
        "period_end": str(end),
        "kpis": {
            "pons_total": total,
            "pons_completed": completed,
            "sla_breaches": breaches,
            "certificate_acceptance_first_pass": first_pass,
            "smmes": smme_count,
        },
        "url": url,
    }
    cache_set(cache_key, resp, ttl_seconds=60)
    return resp

