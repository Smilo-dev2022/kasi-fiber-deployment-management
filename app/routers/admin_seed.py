from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from app.core.deps import get_db, require_roles
from app.scheduler import job_daily_backup, sched


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed", dependencies=[Depends(require_roles("ADMIN"))])
def seed(db: Session = Depends(get_db)):
    # Seed minimal reference data: one ward (PON), one SMME, stock SKUs, and rate cards
    pon_id = str(uuid4())
    smme_id = str(uuid4())

    db.execute(text("insert into smmes (id) values (:id) on conflict do nothing"), {"id": smme_id})
    db.execute(
        text(
            """
        insert into pons (id, status, center_lat, center_lng, geofence_radius_m)
        values (:id, 'Planned', -26.2041, 28.0473, 200)
        on conflict (id) do nothing
        """
        ),
        {"id": pon_id},
    )
    # Note: stock SKU master table not present in current migrations; skip for now
    # Basic rate cards
    for step, unit, cents in (("PolePlanting", "per_pole", 85000), ("Stringing", "per_meter", 250), ("CAC", "per_check", 30000)):
        db.execute(
            text(
                """
            insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from)
            values (gen_random_uuid(), :sm, :st, :u, :r, true, current_date)
            on conflict do nothing
            """
            ),
            {"sm": smme_id, "st": step, "u": unit, "r": cents},
        )
    db.commit()
    return {"ok": True, "pon_id": pon_id, "smme_id": smme_id}


@router.post("/backup", dependencies=[Depends(require_roles("ADMIN"))])
def backup_now():
    url = job_daily_backup()
    if not url:
        raise HTTPException(status_code=500, detail="Backup failed")
    return {"ok": True, "url": url}


@router.get("/jobs", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def list_jobs():
    jobs = [
        {
            "id": j.id,
            "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
            "trigger": str(j.trigger),
        }
        for j in sched.get_jobs()
    ]
    return {"ok": True, "jobs": jobs}

