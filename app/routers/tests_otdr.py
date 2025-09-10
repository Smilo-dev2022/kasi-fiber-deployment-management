from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles


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
    event_distance_m: float | None = None
    cable_register_code: str | None = None


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
    snapped = None
    if payload.event_distance_m and payload.cable_register_code:
        try:
            row = (
                db.execute(
                    text(
                        """
                        select gps_lat, gps_lng
                        from cable_register
                        where code = :c
                        """
                    ),
                    {"c": payload.cable_register_code},
                )
                .mappings()
                .first()
            )
            if row:
                snapped = {"lat": row["gps_lat"], "lng": row["gps_lng"]}
        except Exception:
            snapped = None
    return {"ok": True, "id": oid, "snapped": snapped}


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

