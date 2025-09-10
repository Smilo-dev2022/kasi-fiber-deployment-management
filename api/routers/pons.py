from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.pon import PON
from ..schemas.pon import PONOut, PONCreate, PONUpdate
from ..deps import get_current_user
from ..services.status import update_pon_status
from ..services.audit import audit


router = APIRouter(prefix="/pons", tags=["PONs"])


@router.get("/", response_model=List[PONOut])
def list_pons(
    status: Optional[str] = Query(None),
    ward: Optional[str] = Query(None),
    smme_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(PON)
    if status:
        q = q.filter(PON.status == status)
    if ward:
        q = q.filter(PON.ward == ward)
    if smme_id:
        q = q.filter(PON.smme_id == smme_id)
    if search:
        like = f"%{search}%"
        q = q.filter(PON.pon_number.ilike(like))
    q = q.order_by(PON.created_at.desc())
    return q.all()


@router.post("/", response_model=PONOut)
def create_pon(payload: PONCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pon = PON(
        pon_number=payload.pon_number,
        ward=payload.ward,
        street_area=payload.street_area,
        homes_passed=payload.homes_passed,
        poles_planned=payload.poles_planned,
        smme_id=payload.smme_id,
        created_by=user.id,
    )
    db.add(pon)
    db.commit()
    db.refresh(pon)
    audit(db, "PON", pon.id, "CREATE", user.id, None, {"id": pon.id, "pon_number": pon.pon_number})
    db.commit()
    return pon


@router.get("/{pon_id}", response_model=PONOut)
def get_pon(pon_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pon = db.get(PON, pon_id)
    if not pon:
        raise HTTPException(404, detail="PON not found")
    return pon


@router.patch("/{pon_id}", response_model=PONOut)
def update_pon(pon_id: int, payload: PONUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pon = db.get(PON, pon_id)
    if not pon:
        raise HTTPException(404, detail="PON not found")
    before = {k: getattr(pon, k) for k in ["ward", "street_area", "homes_passed", "poles_planned", "poles_planted"]}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pon, field, value)
    update_pon_status(db, pon)
    db.add(pon)
    db.commit()
    db.refresh(pon)
    after = {k: getattr(pon, k) for k in ["ward", "street_area", "homes_passed", "poles_planned", "poles_planted", "status"]}
    audit(db, "PON", pon.id, "UPDATE", user.id, before, after)
    db.commit()
    return pon


@router.delete("/{pon_id}")
def delete_pon(pon_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pon = db.get(PON, pon_id)
    if not pon:
        raise HTTPException(404, detail="PON not found")
    before = {"pon_number": pon.pon_number}
    db.delete(pon)
    db.commit()
    audit(db, "PON", pon_id, "DELETE", user.id, before, None)
    db.commit()
    return {"message": "Deleted"}

