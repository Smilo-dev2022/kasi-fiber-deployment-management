from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel
from typing import Optional, List
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/stringing-runs", tags=["stringing"])


class RunIn(BaseModel):
    pon_id: str
    team_id: Optional[str] = None
    meters: float
    brackets: int = 0
    dead_ends: int = 0
    tensioners: int = 0
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    photos_ok: bool = False
    qc_passed: bool = False


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_run(payload: RunIn, db: Session = Depends(get_db)):
    rid = str(uuid4())
    db.execute(
        text(
            """
      insert into stringing_runs (id, pon_id, team_id, meters, brackets, dead_ends, tensioners, start_ts, end_ts, photos_ok, qc_passed, created_by, created_at)
      values (:id,:p,:t,:m,:b,:d,:te,:s,:e,:ph,:qc,:cb, now())
    """
        ),
        {
            "id": rid,
            "p": payload.pon_id,
            "t": payload.team_id,
            "m": payload.meters,
            "b": payload.brackets,
            "d": payload.dead_ends,
            "te": payload.tensioners,
            "s": payload.start_ts,
            "e": payload.end_ts,
            "ph": payload.photos_ok,
            "qc": payload.qc_passed,
            "cb": payload.team_id,
        },
    )
    db.commit()
    return {"ok": True, "id": rid}


@router.patch("/{run_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_run(run_id: str, payload: RunIn, db: Session = Depends(get_db)):
    fields = {k: v for k, v in payload.dict().items() if v is not None}
    if not fields:
        return {"ok": True}
    sets = ", ".join([f"{k}=:{k}" for k in fields.keys()])
    fields["id"] = run_id
    db.execute(text(f"update stringing_runs set {sets} where id=:id"), fields)
    db.commit()
    return {"ok": True}


class RunOut(BaseModel):
    id: str
    pon_id: str
    team_id: Optional[str] = None
    meters: float
    brackets: int
    dead_ends: int
    tensioners: int
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    photos_ok: bool
    qc_passed: bool


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_runs(pon_id: str = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text(
                "select * from stringing_runs where pon_id=:p order by created_at desc nulls last"
            ),
            {"p": pon_id},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

