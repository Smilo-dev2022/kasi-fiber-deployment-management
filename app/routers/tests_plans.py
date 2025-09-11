from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel, Field
from app.core.deps import get_db, require_roles


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


def _pon_gated(db: Session, pon_id: str) -> bool:
    """Return True if PON is allowed to complete/invoice based on test results."""
    row = db.execute(
        text(
            """
            with req as (
                select coalesce(bool_or(otdr_required), true) as oreq,
                       coalesce(bool_or(lspm_required), true) as lreq
                from test_plans where pon_id = :p
            ),
            latest_otdr as (
                select tp.id as plan_id, coalesce(bool_and(or2.passed), false) as pass_all
                from test_plans tp
                left join otdr_results or2 on or2.test_plan_id = tp.id
                where tp.pon_id = :p
                group by tp.id
            ),
            latest_lspm as (
                select tp.id as plan_id, coalesce(bool_and(lr.passed), false) as pass_all
                from test_plans tp
                left join lspm_results lr on lr.test_plan_id = tp.id
                where tp.pon_id = :p
                group by tp.id
            )
            select (not (select oreq from req) or (select bool_and(pass_all) from latest_otdr)) as otdr_ok,
                   (not (select lreq from req) or (select bool_and(pass_all) from latest_lspm)) as lspm_ok
            """
        ),
        {"p": pon_id},
    ).mappings().first()
    if not row:
        # No plans means no gating
        return True
    return bool(row["otdr_ok"]) and bool(row["lspm_ok"])

