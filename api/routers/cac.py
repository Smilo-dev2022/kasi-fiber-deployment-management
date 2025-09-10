from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.cac import CACCheck
from ..models.pon import PON
from ..schemas.cac import CACCheckOut, CACCheckCreate
from ..deps import get_current_user
from ..services.status import update_pon_status
from ..services.audit import audit


router = APIRouter(prefix="/pons/{pon_id}/cac", tags=["CAC"])


@router.post("/", response_model=CACCheckOut)
def create_cac(pon_id: int, payload: CACCheckCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if db.get(PON, pon_id) is None:
        raise HTTPException(404, detail="PON not found")
    check = CACCheck(
        pon_id=pon_id,
        pole_number=payload.pole_number,
        pole_length_m=payload.pole_length_m,
        depth_m=payload.depth_m,
        tag_height_m=payload.tag_height_m,
        hook_position=payload.hook_position,
        alignment_ok=payload.alignment_ok,
        comments=payload.comments,
        checked_by=user.id,
        passed=payload.passed,
    )
    db.add(check)
    # Update PON status derived fields
    pon = db.get(PON, pon_id)
    update_pon_status(db, pon)  # type: ignore[arg-type]
    db.commit()
    db.refresh(check)
    audit(db, "CACCheck", check.id, "CREATE", user.id, None, {"passed": check.passed})
    db.commit()
    return check


@router.get("/", response_model=List[CACCheckOut])
def list_cac(pon_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(CACCheck).filter(CACCheck.pon_id == pon_id).all()

