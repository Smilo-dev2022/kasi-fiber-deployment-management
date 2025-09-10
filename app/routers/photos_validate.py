from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from app.core.deps import get_db, require_roles
from app.models.photo import Photo
from app.models.pon import PON
from sqlalchemy import text
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
    if not pon:
        raise HTTPException(400, "PON missing")
    if not p.taken_at and not p.taken_ts:
        raise HTTPException(400, "Missing EXIF DateTime")
    ts = p.taken_ts or p.taken_at
    p.exif_ok = abs((datetime.now(timezone.utc) - ts)) <= timedelta(hours=24)
    if p.gps_lat is None or p.gps_lng is None:
        p.within_geofence = False
    else:
        # Prefer polygon geofence if available
        row = db.execute(
            text(
                "select case when geofence is not null then ST_Contains(geofence, ST_SetSRID(ST_MakePoint(:lng,:lat),4326)) else null end as inside from pons where id = :id"
            ),
            {"id": str(pon.id), "lat": float(p.gps_lat), "lng": float(p.gps_lng)},
        ).first()
        if row and row.inside is not None:
            p.within_geofence = bool(row.inside)
        elif pon.center_lat and pon.center_lng:
            p.within_geofence = (
                distance_m(
                    float(p.gps_lat),
                    float(p.gps_lng),
                    float(pon.center_lat),
                    float(pon.center_lng),
                )
                <= pon.geofence_radius_m
            )
        else:
            p.within_geofence = False
    db.commit()
    return {"ok": True, "exif_ok": p.exif_ok, "within_geofence": p.within_geofence}

