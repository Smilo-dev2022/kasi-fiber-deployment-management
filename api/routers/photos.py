from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.photo import Photo
from ..schemas.photo import PhotoOut, PhotoCreate
from ..deps import get_current_user, get_pon_or_403
from ..services.s3 import get_signed_put_url, create_bucket_if_not_exists
from ..services.status import update_pon_status
from ..services.audit import audit


router = APIRouter(tags=["Photos"])


@router.post("/photos", response_model=PhotoOut)
def create_photo(payload: PhotoCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Access check
    get_pon_or_403(payload.pon_id, db, user)
    photo = Photo(
        pon_id=payload.pon_id,
        task_id=payload.task_id,
        url=str(payload.url),
        kind=payload.kind,
        uploaded_by=user.id,
        taken_at=payload.taken_at,
    )
    db.add(photo)
    # Update PON status after photo
    pon = get_pon_or_403(payload.pon_id, db, user)
    update_pon_status(db, pon)
    db.commit()
    db.refresh(photo)
    audit(db, "Photo", photo.id, "CREATE", user.id, None, {"id": photo.id, "kind": photo.kind})
    db.commit()
    return photo


@router.get("/pons/{pon_id}/photos", response_model=List[PhotoOut])
def list_photos(pon_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    get_pon_or_403(pon_id, db, user)
    return db.query(Photo).filter(Photo.pon_id == pon_id).all()

