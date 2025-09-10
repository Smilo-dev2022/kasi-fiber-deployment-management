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
from app.services.pdf import render_test_pack_pdf
from app.services.s3 import put_bytes


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


class TestPackIn(BaseModel):
    pon_id: str


@router.post("/test-pack", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def generate_test_pack(payload: TestPackIn, db: Session = Depends(get_db)):
    pon = db.get(PON, payload.pon_id)
    if not pon:
        return {"ok": False, "error": "PON not found"}
    # Collect sections via SQL for simplicity
    clos = db.execute(text("select code, gps_lat, gps_lng, status from splice_closures where pon_id=:p"), {"p": payload.pon_id}).mappings().all()
    trays = db.execute(
        text(
            """
        select sc.code as closure, st.tray_no as tray, st.splices_planned as planned, st.splices_done as done
        from splice_trays st join splice_closures sc on sc.id = st.closure_id
        where sc.pon_id = :p order by sc.code, st.tray_no
        """
        ),
        {"p": payload.pon_id},
    ).mappings().all()
    splices = db.execute(
        text(
            """
        select st.tray_no as tray, s.core, s.loss_db as loss, s.passed
        from splices s join splice_trays st on st.id = s.tray_id join splice_closures sc on sc.id = st.closure_id
        where sc.pon_id = :p order by st.tray_no, s.core
        """
        ),
        {"p": payload.pon_id},
    ).mappings().all()
    otdr = db.execute(
        text(
            """
        select tp.link_name as link, or1.wavelength_nm as wl, or1.total_loss_db as loss, or1.event_count as events
        from otdr_results or1 join test_plans tp on tp.id = or1.test_plan_id
        where tp.pon_id = :p
        """
        ),
        {"p": payload.pon_id},
    ).mappings().all()
    lspm = db.execute(
        text(
            """
        select tp.link_name as link, lr.wavelength_nm as wl, lr.measured_loss_db as loss, lr.passed
        from lspm_results lr join test_plans tp on tp.id = lr.test_plan_id
        where tp.pon_id = :p
        """
        ),
        {"p": payload.pon_id},
    ).mappings().all()
    insp = db.execute(
        text(
            """
        select coalesce(sc.code, d.name) as where_, ci.port, coalesce(ci.retest_grade, ci.grade) as grade, ci.passed
        from connector_inspects ci
        left join splice_closures sc on sc.id = ci.closure_id
        left join devices d on d.id = ci.device_id
        where coalesce(sc.pon_id, d.pon_id) = :p
        """
        ),
        {"p": payload.pon_id},
    ).mappings().all()

    meta = {"PON": str(payload.pon_id), "LinkCount": len(otdr) + len(lspm), "GeneratedAt": str(date.today())}
    sections = {
        "Closures": [{"Code": r["code"], "GPS": f"{r['gps_lat']},{r['gps_lng']}", "Status": r["status"]} for r in clos],
        "Trays": [{"Closure": r["closure"], "Tray": r["tray"], "Planned": r["planned"], "Done": r["done"]} for r in trays],
        "Splices": [{"Tray": r["tray"], "Core": r["core"], "Loss dB": r["loss"], "Pass": r["passed"]} for r in splices],
        "OTDR": [{"Link": r["link"], "λ nm": r["wl"], "Loss dB": r["loss"], "Events": r["events"]} for r in otdr],
        "LSPM": [{"Link": r["link"], "λ nm": r["wl"], "Loss dB": r["loss"], "Pass": r["passed"]} for r in lspm],
        "Inspect": [{"Where": r["where_"], "Port": r["port"], "Grade": r["grade"], "Pass": r["passed"]} for r in insp],
    }
    pdf = render_test_pack_pdf(meta, sections)
    key = f"reports/test-packs/{payload.pon_id}.pdf"
    url = put_bytes(key, "application/pdf", pdf)
    # attach on PON for convenience if pons table has link column; otherwise just return url
    # Acceptance checks quick summary
    # 1) Splice average loss per tray under 0.15 dB
    avg_rows = db.execute(
        text(
            """
        select st.id as tray_id, avg(s.loss_db)::numeric(5,3) as avg_loss
        from splice_trays st
        join splice_closures sc on sc.id = st.closure_id
        join splices s on s.tray_id = st.id
        where sc.pon_id = :p and s.loss_db is not null
        group by st.id
        """
        ),
        {"p": payload.pon_id},
    ).mappings().all()
    splices_ok = all(float(r["avg_loss"]) <= 0.15 for r in avg_rows) if avg_rows else True

    # 2) All required LSPM links pass within budget
    req_rows = db.execute(
        text(
            """
        select count(1)
        from test_plans tp
        left join (
          select test_plan_id, bool_or(passed) as ok from lspm_results group by test_plan_id
        ) l on l.test_plan_id = tp.id
        where tp.pon_id = :p and tp.lspm_required and coalesce(l.ok,false)=false
        """
        ),
        {"p": payload.pon_id},
    ).first()
    lspm_ok = (req_rows[0] == 0)

    # 3) OTDR event count matches plan within tolerance - simplified: ensure at least one result per required plan
    otdr_req = db.execute(text("select count(1) from test_plans where pon_id=:p and otdr_required"), {"p": payload.pon_id}).first()[0]
    otdr_have = db.execute(
        text(
            "select count(distinct tp.id) from otdr_results or1 join test_plans tp on tp.id=or1.test_plan_id where tp.pon_id=:p"
        ),
        {"p": payload.pon_id},
    ).first()[0]
    otdr_ok = otdr_have >= otdr_req

    # 4) Photos validated - ensure some test photos are within geofence and exif ok
    photos_ok = db.execute(
        text("select count(1) from test_photos where within_geofence=true and exif_ok=true"),
        {},
    ).first()[0] > 0

    return {"ok": True, "url": url, "checks": {"splices_avg_ok": splices_ok, "lspm_ok": lspm_ok, "otdr_ok": otdr_ok, "photos_ok": photos_ok}}


