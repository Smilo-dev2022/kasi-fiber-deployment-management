from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles
from app.services.geo import snap_distance_to_cable


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


class OTDRImportIn(BaseModel):
    pon_id: str
    olt_port: str
    event_distance_m: float = Field(ge=0.0, le=100000.0)
    cable_hint: str | None = None


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
    return {"ok": True, "id": oid}


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


@router.post("/import", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def import_otdr(payload: OTDRImportIn, db: Session = Depends(get_db)):
    # Read cable polylines for the PON
    cables = (
        db.execute(
            text("select id::text, code, type, polyline from cable_register where pon_id = :pon"),
            {"pon": payload.pon_id},
        )
        .mappings()
        .all()
    )
    if not cables:
        raise HTTPException(400, "No cable register for PON")
    snapped = snap_distance_to_cable(payload.event_distance_m, [dict(r) for r in cables], payload.cable_hint)
    if not snapped:
        raise HTTPException(400, "Unable to snap distance to cable")
    return {"ok": True, "cable_id": snapped["cable_id"], "near_lat": snapped["lat"], "near_lng": snapped["lng"], "chainage_m": snapped["chainage_m"]}

