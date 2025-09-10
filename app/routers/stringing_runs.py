from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4

from app.core.deps import get_db, require_roles
from app.models.stringing import StringingRun
from app.models.photo import Photo


router = APIRouter(prefix="/stringing-runs", tags=["stringing-runs"])


class StringingRunIn(BaseModel):
    pon_id: str
    meters: float = Field(ge=0)
    brackets: Optional[int] = 0
    dead_ends: Optional[int] = 0
    tensioners: Optional[int] = 0
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def create_stringing_run(payload: StringingRunIn, db: Session = Depends(get_db)):
    pon_uuid = UUID(payload.pon_id)

    # Guards: required photos with tags
    required_tags = {"StringingStart", "Brackets", "Tension", "DeadEnds", "Completion"}
    tags_ok = (
        db.query(Photo)
        .filter(Photo.pon_id == pon_uuid)
        .filter(Photo.exif_ok.is_(True))
        .filter(Photo.within_geofence.is_(True))
        .filter(Photo.tags.overlap(list(required_tags)))
        .count()
    )
    if tags_ok < len(required_tags):
        raise HTTPException(400, "Required photos with tags missing or invalid")

    row = StringingRun(
        id=uuid4(),
        pon_id=pon_uuid,
        meters=payload.meters,
        brackets=payload.brackets or 0,
        dead_ends=payload.dead_ends or 0,
        tensioners=payload.tensioners or 0,
        photos_ok=True,
    )
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_stringing_runs(pon_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(StringingRun)
    if pon_id:
        q = q.filter(StringingRun.pon_id == UUID(pon_id))
    rows: List[StringingRun] = q.order_by(StringingRun.start_ts).all()
    return [
        {
            "id": str(r.id),
            "pon_id": str(r.pon_id),
            "meters": float(r.meters),
            "brackets": r.brackets or 0,
            "dead_ends": r.dead_ends or 0,
            "tensioners": r.tensioners or 0,
            "start_ts": r.start_ts.isoformat() if r.start_ts else None,
            "end_ts": r.end_ts.isoformat() if r.end_ts else None,
            "photos_ok": bool(r.photos_ok),
            "qc_passed": bool(r.qc_passed),
        }
        for r in rows
    ]


class StringingRunPatch(BaseModel):
    meters: Optional[float] = Field(default=None, ge=0)
    photos_ok: Optional[bool] = None
    qc_passed: Optional[bool] = None


@router.patch("/{run_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_stringing_run(run_id: str, payload: StringingRunPatch, db: Session = Depends(get_db)):
    row = db.get(StringingRun, UUID(run_id))
    if not row:
        raise HTTPException(404, "Not found")

    if payload.meters is not None:
        row.meters = payload.meters
    if payload.photos_ok is not None:
        row.photos_ok = payload.photos_ok
    if payload.qc_passed is not None:
        row.qc_passed = payload.qc_passed

    db.commit()
    return {"ok": True}

