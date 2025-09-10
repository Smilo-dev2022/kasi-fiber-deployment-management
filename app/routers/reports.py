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
from sqlalchemy import func, text


router = APIRouter(prefix="/reports", tags=["reports"])


class WeeklyIn(BaseModel):
    start: date | None = None
    end: date | None = None


@router.post("/weekly", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def weekly(payload: WeeklyIn, db: Session = Depends(get_db)):
    start = payload.start or (date.today() - timedelta(days=7))
    end = payload.end or date.today()
    total = db.query(func.count(PON.id)).scalar()
    completed = db.query(func.count(PON.id)).filter(PON.status == "Completed").scalar()
    breaches = db.query(func.count(Task.id)).filter(Task.breached == True).scalar()
    first_pass = db.query(func.count(CACCheck.id)).filter(CACCheck.passed == True).scalar()
    smme_count = db.query(func.count(SMME.id)).scalar()
    url = f"https://example.local/reports/{uuid4()}.pdf"
    db.execute(
        text(
            "insert into reports (id, kind, period_start, period_end, url) values (gen_random_uuid(), 'WeeklyExec', :s, :e, :u)"
        ),
        {"s": start, "e": end, "u": url},
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


@router.get("/uptime-by-ward", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "AUDITOR"))])
def uptime_by_ward(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                """
                select p.ward_id,
                       count(*) filter (where i.status in ('Open','Acknowledged')) as active_incidents,
                       count(*) as total_incidents
                from pons p
                left join incidents i on i.pon_id = p.id
                group by p.ward_id
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


@router.get("/incidents-by-category", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "AUDITOR"))])
def active_incidents(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                """
                select category, assigned_org_id, count(*) as total
                from incidents
                where status in ('Open','Acknowledged')
                group by category, assigned_org_id
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


@router.get("/sla-breaches", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "AUDITOR"))])
def sla_breaches(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                """
                select t.pon_id, count(*) as breaches
                from tasks t
                where t.breached = true
                group by t.pon_id
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

