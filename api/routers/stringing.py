from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.stringing import StringingRun
from ..models.pon import PON
from ..schemas.stringing import StringingRunOut, StringingRunCreate
from ..deps import get_current_user
from ..services.status import update_pon_status
from ..services.audit import audit


router = APIRouter(prefix="/pons/{pon_id}/stringing", tags=["Stringing"])


@router.post("/", response_model=StringingRunOut)
def create_run(pon_id: int, payload: StringingRunCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if db.get(PON, pon_id) is None:
        raise HTTPException(404, detail="PON not found")
    run = StringingRun(
        pon_id=pon_id,
        meters=payload.meters,
        brackets=payload.brackets,
        dead_ends=payload.dead_ends,
        tensioner=payload.tensioner,
        completed_by=user.id,
    )
    db.add(run)
    pon = db.get(PON, pon_id)
    update_pon_status(db, pon)  # type: ignore[arg-type]
    db.commit()
    db.refresh(run)
    audit(db, "StringingRun", run.id, "CREATE", user.id, None, {"meters": run.meters})
    db.commit()
    return run


@router.get("/", response_model=List[StringingRunOut])
def list_runs(pon_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(StringingRun).filter(StringingRun.pon_id == pon_id).all()

