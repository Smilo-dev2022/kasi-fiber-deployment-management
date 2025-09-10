from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

from app.core.deps import get_db, require_roles
from app.core.limiter import limiter, key_by_org
from app.models.certificate_acceptance import CertificateAcceptance
from app.models.photo import Photo


router = APIRouter(prefix="/certificate-acceptance", tags=["certificate-acceptance"])


class CertificateAcceptanceIn(BaseModel):
    pon_id: str
    pole_number: Optional[str] = None
    pole_length_m: float = Field(ge=7.4, le=7.8)
    depth_m: float = Field(ge=1.1, le=1.2)
    tag_height_m: float = Field(ge=2.2, le=2.3)
    hook_position: Optional[str] = None
    alignment_ok: bool = True
    comments: Optional[str] = None
    passed: bool = True
    checked_by: Optional[str] = None


@router.post(
    "",
    dependencies=[Depends(require_roles("ADMIN", "PM", "SITE")), Depends(limiter(120, 60, key_by_org))],
)
def create_certificate_acceptance(payload: CertificateAcceptanceIn, db: Session = Depends(get_db)):
    # Guard: require at least one validated photo (EXIF and geofence OK) for the PON
    has_valid_photo = (
        db.query(Photo)
        .filter(Photo.pon_id == UUID(payload.pon_id))
        .filter(Photo.exif_ok == True)
        .filter(Photo.within_geofence == True)
        .first()
        is not None
    )
    if not has_valid_photo:
        raise HTTPException(400, "Validated photo required (EXIF and geofence)")

    rec = CertificateAcceptance(
        pon_id=UUID(payload.pon_id),
        pole_number=payload.pole_number,
        pole_length_m=payload.pole_length_m,
        depth_m=payload.depth_m,
        tag_height_m=payload.tag_height_m,
        hook_position=payload.hook_position,
        alignment_ok=payload.alignment_ok,
        comments=payload.comments,
        passed=payload.passed,
        checked_by=UUID(payload.checked_by) if payload.checked_by else None,
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "id": str(rec.id)}


class CertificateAcceptanceOut(BaseModel):
    id: str
    pon_id: str
    pole_number: Optional[str]
    pole_length_m: float
    depth_m: float
    tag_height_m: float
    hook_position: Optional[str]
    alignment_ok: bool
    comments: Optional[str]
    passed: bool


@router.get("", response_model=List[CertificateAcceptanceOut], dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_certificate_acceptance(pon_id: str = Query(...), db: Session = Depends(get_db)):
    rows = (
        db.query(CertificateAcceptance)
        .filter(CertificateAcceptance.pon_id == UUID(pon_id))
        .order_by(CertificateAcceptance.checked_at.desc().nullslast())
        .all()
    )
    return [
        CertificateAcceptanceOut(
            id=str(r.id),
            pon_id=str(r.pon_id),
            pole_number=r.pole_number,
            pole_length_m=float(r.pole_length_m),
            depth_m=float(r.depth_m),
            tag_height_m=float(r.tag_height_m),
            hook_position=r.hook_position,
            alignment_ok=bool(r.alignment_ok),
            comments=r.comments,
            passed=bool(r.passed),
        )
        for r in rows
    ]

