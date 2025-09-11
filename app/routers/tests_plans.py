from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles
from sqlalchemy import and_


router = APIRouter(prefix="/tests/plans", tags=["tests"])


class PlanIn(BaseModel):
    pon_id: str
    link_name: str
    from_point: str
    to_point: str
    wavelength_nm: int = Field(ge=1260, le=1650)
    max_loss_db: float = Field(ge=0.1, le=30.0)
    otdr_required: bool = True
    lspm_required: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_plan(payload: PlanIn, db: Session = Depends(get_db)):
    pid = str(uuid4())
    db.execute(
        text(
            """
      insert into test_plans (id, pon_id, link_name, from_point, to_point, wavelength_nm, max_loss_db, otdr_required, lspm_required)
      values (:id, :pon, :ln, :fp, :tp, :wl, :maxl, :ot, :ls)
    """
        ),
        {
            "id": pid,
            "pon": payload.pon_id,
            "ln": payload.link_name,
            "fp": payload.from_point,
            "tp": payload.to_point,
            "wl": payload.wavelength_nm,
            "maxl": payload.max_loss_db,
            "ot": payload.otdr_required,
            "ls": payload.lspm_required,
        },
    )
    db.commit()
    return {"ok": True, "id": pid}


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_plans(pon_id: str = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text("select * from test_plans where pon_id = :p order by link_name"),
            {"p": pon_id},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

