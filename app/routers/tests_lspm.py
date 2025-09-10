from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/tests/lspm", tags=["tests"])


class LSPMIn(BaseModel):
    test_plan_id: str
    wavelength_nm: int = Field(ge=1260, le=1650)
    measured_loss_db: float = Field(ge=0.0, le=30.0)
    margin_db: float | None = Field(default=None, ge=-10.0, le=10.0)
    passed: bool = False


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def add_lspm(payload: LSPMIn, db: Session = Depends(get_db)):
    lid = str(uuid4())
    db.execute(
        text(
            """
      insert into lspm_results (id, test_plan_id, wavelength_nm, measured_loss_db, margin_db, tested_at, passed)
      values (:id, :tp, :wl, :ml, :mg, now(), :p)
    """
        ),
        {
            "id": lid,
            "tp": payload.test_plan_id,
            "wl": payload.wavelength_nm,
            "ml": payload.measured_loss_db,
            "mg": payload.margin_db,
            "p": payload.passed,
        },
    )
    db.commit()
    return {"ok": True, "id": lid}


@router.get("/by-plan/{plan_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_lspm(plan_id: str, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text("select * from lspm_results where test_plan_id = :p order by tested_at desc"),
            {"p": plan_id},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

