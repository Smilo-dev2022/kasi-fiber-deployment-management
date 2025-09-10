from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles
from typing import List, Optional


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


class OTDRImportEvent(BaseModel):
    distance_m: float = Field(ge=0)
    event_type: Optional[str] = None
    loss_db: Optional[float] = None


class OTDRImportIn(BaseModel):
    otdr_result_id: str
    events: List[OTDRImportEvent]


@router.post("/import", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def import_otdr(payload: OTDRImportIn, db: Session = Depends(get_db)):
    # Insert events
    for ev in payload.events:
        db.execute(
            text(
                """
            insert into otdr_events (id, otdr_result_id, distance_m, event_type, loss_db)
            values (gen_random_uuid(), :rid, :dist, :type, :loss)
            """
            ),
            {"rid": payload.otdr_result_id, "dist": ev.distance_m, "type": ev.event_type, "loss": ev.loss_db},
        )

    # Snap to nearest trench segment polyline by distance if possible
    # Approximated by selecting nearest closure/trench along same PON using distance_m heuristics (placeholder)
    # Detailed GIS snapping would be implemented with PostGIS; here we record events only.
    db.commit()
    return {"ok": True, "count": len(payload.events)}

