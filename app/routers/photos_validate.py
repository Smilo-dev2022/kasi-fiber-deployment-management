from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from app.core.deps import get_db, require_roles
from app.models.photo import Photo
from app.utils.exif import extract_gps_and_datetime
from app.models.pon import PON
from app.services.status_engine import recompute_pon_status
import math


router = APIRouter(prefix="/photos", tags=["photos"])


class ValidateIn(BaseModel):
    photo_id: str


def distance_m(a_lat, a_lng, b_lat, b_lng):
    R = 6371000.0
    phi1 = math.radians(a_lat)
    phi2 = math.radians(b_lat)
    dphi = math.radians(b_lat - a_lat)
    dlmb = math.radians(b_lng - a_lng)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


@router.post("/validate", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def validate_photo(payload: ValidateIn, db: Session = Depends(get_db)):
    from uuid import UUID

    p = db.get(Photo, UUID(payload.photo_id))
    if not p:
        raise HTTPException(404, "Not found")
    pon = db.get(PON, p.pon_id)
    if not pon or not pon.center_lat or not pon.center_lng:
        raise HTTPException(400, "PON geofence missing")
    if not p.taken_at and not p.taken_ts:
        raise HTTPException(400, "Missing EXIF DateTime")
    ts = p.taken_ts or p.taken_at
    p.exif_ok = abs((datetime.now(timezone.utc) - ts)) <= timedelta(hours=24)
    if p.gps_lat is None or p.gps_lng is None:
        p.within_geofence = False
    else:
        p.within_geofence = (
            distance_m(
                float(p.gps_lat),
                float(p.gps_lng),
                float(pon.center_lat),
                float(pon.center_lng),
            )
            <= pon.geofence_radius_m
        )
    db.commit()
    if p.pon_id:
        recompute_pon_status(db, p.pon_id)
    return {"ok": True, "exif_ok": p.exif_ok, "within_geofence": p.within_geofence}


ALLOWED_UPLOAD_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/upload", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
async def upload_photo(pon_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400, "Unsupported file type")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File too large")

    from uuid import uuid4, UUID

    photo = Photo(id=uuid4(), pon_id=UUID(pon_id))

    if file.content_type in ("image/jpeg", "image/png"):
        lat, lng, dt = extract_gps_and_datetime(data)
        photo.gps_lat = lat
        photo.gps_lng = lng
        photo.taken_ts = dt

    db.add(photo)
    db.commit()
    return {"ok": True, "photo_id": str(photo.id)}

