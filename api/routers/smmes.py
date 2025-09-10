from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.smme import SMME
from ..schemas.smme import SMMEOut, SMMECreate, SMMEUpdate
from ..deps import get_current_user
from ..services.audit import audit


router = APIRouter(prefix="/smmes", tags=["SMMEs"])


@router.get("/", response_model=List[SMMEOut])
def list_smmes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(SMME).order_by(SMME.name).all()


@router.post("/", response_model=SMMEOut)
def create_smme(payload: SMMECreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    smme = SMME(
        name=payload.name,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        contact_email=payload.contact_email,
        active=payload.active,
    )
    db.add(smme)
    db.commit()
    db.refresh(smme)
    audit(db, "SMME", smme.id, "CREATE", user.id, None, {"name": smme.name})
    db.commit()
    return smme


@router.patch("/{smme_id}", response_model=SMMEOut)
def update_smme(smme_id: int, payload: SMMEUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    smme = db.get(SMME, smme_id)
    if not smme:
        raise Exception("SMME not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(smme, k, v)
    db.add(smme)
    db.commit()
    db.refresh(smme)
    audit(db, "SMME", smme.id, "UPDATE", user.id, None, payload.model_dump(exclude_unset=True))
    db.commit()
    return smme

