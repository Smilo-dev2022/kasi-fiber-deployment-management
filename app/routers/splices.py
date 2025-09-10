from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/splices", tags=["splices"])


class SpliceIn(BaseModel):
    tray_id: str
    core: int = Field(ge=1)
    from_cable: Optional[str] = None
    to_cable: Optional[str] = None
    loss_db: Optional[float] = Field(default=None, ge=0.0, le=3.0)
    method: Optional[str] = None  # fusion or mechanical
    tech_id: Optional[str] = None
    passed: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def add_splice(payload: SpliceIn, db: Session = Depends(get_db)):
    sid = str(uuid4())
    db.execute(
        text(
            """
      insert into splices (id, tray_id, core, from_cable, to_cable, loss_db, method, tech_id, time, passed)
      values (:id, :t, :c, :fc, :tc, :l, :m, :tech, now(), :p)
    """
        ),
        {
            "id": sid,
            "t": payload.tray_id,
            "c": payload.core,
            "fc": payload.from_cable,
            "tc": payload.to_cable,
            "l": payload.loss_db,
            "m": payload.method,
            "tech": payload.tech_id,
            "p": payload.passed,
        },
    )
    # bump trays.splices_done
    db.execute(
        text("update splice_trays set splices_done = coalesce(splices_done,0) + 1 where id = :t"),
        {"t": payload.tray_id},
    )
    db.commit()
    return {"ok": True, "id": sid}


@router.get("/by-tray/{tray_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_splices(tray_id: str, db: Session = Depends(get_db)):
    rows = (
        db.execute(text("select * from splices where tray_id = :t order by core"), {"t": tray_id})
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


class SplicePatch(BaseModel):
    loss_db: Optional[float] = Field(default=None, ge=0.0, le=3.0)
    passed: Optional[bool] = None
    method: Optional[str] = None


@router.patch("/{splice_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_splice(splice_id: str, payload: SplicePatch, db: Session = Depends(get_db)):
    fields = payload.dict(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No fields")
    sets = ", ".join([f"{k} = :{k}" for k in fields.keys()])
    fields["id"] = splice_id
    db.execute(text(f"update splices set {sets} where id = :id"), fields)
    db.commit()
    return {"ok": True}

