from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.deps import get_db, require_roles
from app.models.pon import PON
from app.schemas.pon import PONCreate, PONOut, PONUpdate
from app.services.status import compute_status


router = APIRouter(prefix="/pons", tags=["pons"])


@router.get("", response_model=List[PONOut])
def list_pons(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    ward: Optional[str] = Query(None),
    smme_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    qset = db.query(PON)
    if status:
        qset = qset.filter(PON.status == status)
    if ward:
        qset = qset.filter(PON.ward == ward)
    if smme_id:
        from uuid import UUID
        qset = qset.filter(PON.smme_id == UUID(smme_id))
    if q:
        like = f"%{q}%"
        qset = qset.filter(PON.pon_number.ilike(like))
    return qset.order_by(PON.pon_number).all()


@router.post("", response_model=PONOut, dependencies=[Depends(require_roles("ADMIN","PM"))])
def create_pon(payload: PONCreate, db: Session = Depends(get_db)):
    pon = PON(**payload.dict())
    db.add(pon)
    db.commit()
    db.refresh(pon)
    return pon


@router.get("/{pon_id}", response_model=PONOut)
def get_pon(pon_id: str, db: Session = Depends(get_db)):
    from uuid import UUID
    pon = db.get(PON, UUID(pon_id))
    if not pon:
        raise HTTPException(status_code=404, detail="Not found")
    return pon


@router.patch("/{pon_id}", response_model=PONOut, dependencies=[Depends(require_roles("ADMIN","PM","SITE"))])
def update_pon(pon_id: str, payload: PONUpdate, db: Session = Depends(get_db)):
    from uuid import UUID
    pon = db.get(PON, UUID(pon_id))
    if not pon:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(pon, k, v)
    pon.status = compute_status(db, pon)
    db.commit()
    db.refresh(pon)
    return pon
