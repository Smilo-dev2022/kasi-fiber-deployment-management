from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/tests/otdr", tags=["tests"])


class OTDRIn(BaseModel):
    test_plan_id: str
    file_url: str
    vendor: Optional[str] = None
    wavelength_nm: int = Field(ge=1260, le=1650)
    total_loss_db: Optional[float] = Field(default=None, ge=0.0, le=30.0)
    event_count: Optional[int] = None
    max_splice_loss_db: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    back_reflection_db: Optional[float] = Field(default=None, ge=-80.0, le=-20.0)
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

