from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from pydantic import BaseModel
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/closures", tags=["trays"])


class TrayIn(BaseModel):
    tray_no: int
    fiber_start: int | None = None
    fiber_end: int | None = None
    splices_planned: int | None = None


@router.post("/{closure_id}/trays", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def add_tray(closure_id: str, payload: TrayIn, db: Session = Depends(get_db)):
    tid = str(uuid4())
    db.execute(
        text(
            """
      insert into splice_trays (id, closure_id, tray_no, fiber_start, fiber_end, splices_planned)
      values (:id, :c, :no, :fs, :fe, :sp)
    """
        ),
        {
            "id": tid,
            "c": closure_id,
            "no": payload.tray_no,
            "fs": payload.fiber_start,
            "fe": payload.fiber_end,
            "sp": payload.splices_planned,
        },
    )
    db.commit()
    return {"ok": True, "id": tid}


@router.get("/{closure_id}/trays", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_trays(closure_id: str, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            text("select * from splice_trays where closure_id = :c order by tray_no"),
            {"c": closure_id},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]

