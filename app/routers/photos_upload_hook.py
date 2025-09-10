from fastapi import APIRouter, Depends, HTTPException
import os
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.core.deps import get_db, require_roles
from app.core.limiter import limiter, key_by_org
from app.models.photo import Photo
from app.models.pon import PON
from app.services.s3 import get_object_bytes, head_object, settings
from app.services.exif import parse_exif


router = APIRouter(prefix="/photos", tags=["photos"])


class RegisterIn(BaseModel):
    photo_id: str
    s3_key: str


def dist_m(a_lat, a_lng, b_lat, b_lng):
    R = 6371000.0
    from math import radians, sin, cos, asin, sqrt

    phi1, phi2 = radians(a_lat), radians(b_lat)
    dphi = radians(b_lat - a_lat)
    dlmb = radians(b_lng - a_lng)
    h = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
    return 2 * R * asin(sqrt(h))


HEAVY_WRITE_PER_MIN = int(os.getenv("HEAVY_WRITE_PER_ORG_PER_MIN", "120"))
HEAVY_WRITE_WINDOW_SEC = int(os.getenv("HEAVY_WRITE_WINDOW_SEC", "60"))


@router.post(
    "/register",
    dependencies=[
        Depends(require_roles("ADMIN", "PM", "SITE", "SMME")),
        Depends(limiter(limit=HEAVY_WRITE_PER_MIN, window_sec=HEAVY_WRITE_WINDOW_SEC, key_fn=key_by_org)),
    ],
)
def register(payload: RegisterIn, db: Session = Depends(get_db), request: Request = None):
    p: Photo | None = db.get(Photo, UUID(payload.photo_id))
    if not p:
        raise HTTPException(404, "Photo not found")

    # Validate S3 object metadata for size/type
    try:
        meta = head_object(payload.s3_key)
    except Exception:
        raise HTTPException(404, "S3 object not found")
    ctype = (meta.get("ContentType") or "").lower()
    size = int(meta.get("ContentLength") or 0)
    if settings.ALLOWED_CONTENT_TYPES and ctype not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, f"Unsupported Content-Type: {ctype}")
    if size <= 0 or size > settings.FILE_MAX_BYTES:
        raise HTTPException(413, "File too large")

    # Read from S3 and parse EXIF
    blob = get_object_bytes(payload.s3_key)
    meta = parse_exif(blob)

    # Update photo with EXIF
    p.taken_ts = meta["taken_ts"]
    p.gps_lat = meta["gps_lat"]
    p.gps_lng = meta["gps_lng"]

    # Validate timing and geofence if PON has center
    exif_ok = False
    within = False
    if p.taken_ts:
        exif_ok = abs((datetime.now(timezone.utc) - p.taken_ts)) <= timedelta(hours=24)
    pon: PON | None = db.get(PON, p.pon_id)
    if (
        pon
        and pon.center_lat
        and pon.center_lng
        and p.gps_lat is not None
        and p.gps_lng is not None
    ):
        within = (
            dist_m(
                float(p.gps_lat),
                float(p.gps_lng),
                float(pon.center_lat),
                float(pon.center_lng),
            )
            <= pon.geofence_radius_m
        )

    p.exif_ok = exif_ok
    p.within_geofence = within
    db.commit()
    return {"ok": True, "exif_ok": exif_ok, "within_geofence": within}

