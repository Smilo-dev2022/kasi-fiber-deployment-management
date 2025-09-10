from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.core.deps import get_db, require_roles
from app.models.cac import CACCheck
from app.models.photo import Photo
from app.services.status_engine import recompute_pon_status


router = APIRouter(prefix="/cac", tags=["cac"])


class CACIn(BaseModel):
    pon_id: str
    pole_number: Optional[str] = None
    pole_length_m: float = Field(ge=7.4, le=7.8)
    depth_m: float = Field(ge=1.1, le=1.2)
    tag_height_m: float = Field(ge=2.2, le=2.3)
    hook_position: Optional[str] = None
    alignment_ok: bool = True
    comments: Optional[str] = None
    passed: bool = True


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_cac(payload: CACIn, db: Session = Depends(get_db)):
    from uuid import UUID

    # Block completion if within_geofence is false (no validated photo)
    has_valid_photo = (
        db.query(Photo.id).filter(
            Photo.pon_id == UUID(payload.pon_id), Photo.within_geofence == True, Photo.exif_ok == True
        ).first()
        is not None
    )
    if not has_valid_photo:
        raise HTTPException(400, "Geofence not validated")

    rec = CACCheck(
        pon_id=UUID(payload.pon_id),
        pole_number=payload.pole_number,
        pole_length_m=payload.pole_length_m,
        depth_m=payload.depth_m,
        tag_height_m=payload.tag_height_m,
        hook_position=payload.hook_position,
        alignment_ok=payload.alignment_ok,
        comments=payload.comments,
        passed=payload.passed,
    )
    db.add(rec)
    db.commit()
    # Status engine
    recompute_pon_status(db, rec.pon_id)
    return {"ok": True, "id": str(rec.id)}

