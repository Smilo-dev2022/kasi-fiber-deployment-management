from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.deps import get_db, require_roles
from app.models.cac import CertificateAcceptance
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


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_certificate_acceptance(payload: CertificateAcceptanceIn, db: Session = Depends(get_db)):
    from uuid import UUID

    # Guard: require at least one valid photo for this PON with EXIF OK and within geofence
    photos = (
        db.query(Photo)
        .filter(Photo.pon_id == UUID(payload.pon_id))
        .filter(Photo.exif_ok.is_(True))
        .filter(Photo.within_geofence.is_(True))
        .limit(1)
        .all()
    )
    if not photos:
        raise HTTPException(400, "At least one valid photo (EXIF/GPS) required")

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
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "id": str(rec.id)}


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_certificate_acceptance(pon_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    from uuid import UUID

    q = db.query(CertificateAcceptance)
    if pon_id:
        q = q.filter(CertificateAcceptance.pon_id == UUID(pon_id))
    rows: List[CertificateAcceptance] = q.all()
    return [
        {
            "id": str(r.id),
            "pon_id": str(r.pon_id),
            "pole_number": r.pole_number,
            "pole_length_m": float(r.pole_length_m),
            "depth_m": float(r.depth_m),
            "tag_height_m": float(r.tag_height_m),
            "hook_position": r.hook_position,
            "alignment_ok": bool(r.alignment_ok),
            "comments": r.comments,
            "passed": bool(r.passed),
            "checked_by": str(r.checked_by) if r.checked_by else None,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        }
        for r in rows
    ]

