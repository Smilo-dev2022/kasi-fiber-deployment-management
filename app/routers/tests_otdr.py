from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles
from typing import List
from math import isfinite
from app.models.topology_ext import CableRegister


router = APIRouter(prefix="/tests/otdr", tags=["tests"])


class OTDRIn(BaseModel):
    test_plan_id: str
    file_url: str
    vendor: str | None = None
    wavelength_nm: int = Field(ge=1260, le=1650)
    total_loss_db: float | None = Field(default=None, ge=0.0, le=30.0)
    event_count: int | None = None
    max_splice_loss_db: float | None = Field(default=None, ge=0.0, le=5.0)
    back_reflection_db: float | None = Field(default=None, ge=-80.0, le=-20.0)
    passed: bool = False
    # Optional parsed events: distance_m values to snap
    events_distance_m: List[float] | None = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def add_otdr(payload: OTDRIn, db: Session = Depends(get_db)):
    oid = str(uuid4())
    db.execute(
        text(
            """
      insert into otdr_results (id, test_plan_id, file_url, vendor, wavelength_nm, total_loss_db, event_count, max_splice_loss_db, back_reflection_db, tested_at, passed)
      values (:id, :tp, :url, :v, :wl, :tl, :ec, :ms, :br, now(), :p)
    """
        ),
        {
            "id": oid,
            "tp": payload.test_plan_id,
            "url": payload.file_url,
            "v": payload.vendor,
            "wl": payload.wavelength_nm,
            "tl": payload.total_loss_db,
            "ec": payload.event_count,
            "ms": payload.max_splice_loss_db,
            "br": payload.back_reflection_db,
            "p": payload.passed,
        },
    )
    db.commit()
    # Optional: insert snapped OTDR events
    if payload.events_distance_m:
        # Get candidate cable polyline for the plan's PON
        row = db.execute(text("select p.pon_id from test_plans tp join pons p on tp.pon_id = p.id where tp.id = :tp"), {"tp": payload.test_plan_id}).first()
        pon_id = row[0] if row else None
        cable = (
            db.query(CableRegister)
            .filter(CableRegister.pon_id == pon_id)
            .order_by(CableRegister.length_m.desc().nullslast())
            .first()
        )
        if cable and cable.polyline:
            import json
            try:
                coords = json.loads(cable.polyline)
            except Exception:
                coords = []
            def snap_distance_to_polyline(dist_m: float):
                # naive proportional snap along polyline by chainage
                if not coords or not isfinite(dist_m):
                    return None
                total = float(cable.length_m or 0)
                if total <= 0:
                    return None
                t = max(0.0, min(1.0, dist_m / total))
                idx = int(t * (len(coords) - 1))
                lat, lng = coords[idx]
                return lat, lng
            for d in payload.events_distance_m:
                snapped = snap_distance_to_polyline(d)
                if snapped:
                    db.execute(
                        text(
                            "insert into otdr_events (id, otdr_result_id, distance_m, gps_lat, gps_lng, created_at) values (gen_random_uuid(), :rid, :dist, :lat, :lng, now())"
                        ),
                        {"rid": oid, "dist": d, "lat": snapped[0], "lng": snapped[1]},
                    )
            db.commit()
    return {"ok": True, "id": oid}


@router.post("/import", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def import_otdr(payload: OTDRIn, db: Session = Depends(get_db)):
    return add_otdr(payload, db)


@router.get("/by-plan/{plan_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_otdr(plan_id: str, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text("select * from otdr_results where test_plan_id = :p order by tested_at desc"),
            {"p": plan_id},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

