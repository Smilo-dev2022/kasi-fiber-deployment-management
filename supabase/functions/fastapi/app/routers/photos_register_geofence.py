from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/photos", tags=["photos"])


class PhotoGeoIn(BaseModel):
    photo_id: str


@router.post("/register-geo", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def register_geo(payload: PhotoGeoIn, db: Session = Depends(get_db)):
    # Validate against polygon geofence when present, else fallback to center+radius
    row = (
        db.execute(
            text(
                """
                select p.id as pid, p.pon_id, p.gps_lat, p.gps_lng,
                       x.center_lat, x.center_lng, x.geofence_radius_m, x.geofence_geom
                from photos p
                join pons x on x.id = p.pon_id
                where p.id = :pid
                """
            ),
            {"pid": str(UUID(payload.photo_id))},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Photo not found")

    within = False
    if row["gps_lat"] is not None and row["gps_lng"] is not None:
        if row["geofence_geom"] is not None:
            within = (
                db.execute(
                    text(
                        "select ST_Contains(:poly::geometry, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) as ok"
                    ),
                    {"poly": row["geofence_geom"], "lat": float(row["gps_lat"]), "lng": float(row["gps_lng"])},
                )
                .mappings()
                .first()["ok"]
            )
        elif row["center_lat"] and row["center_lng"] and row["geofence_radius_m"]:
            # radius check in meters via ST_DistanceSphere
            within = (
                db.execute(
                    text(
                        "select ST_DistanceSphere(ST_SetSRID(ST_MakePoint(:lng, :lat),4326), ST_SetSRID(ST_MakePoint(:clng, :clat),4326)) <= :m as ok"
                    ),
                    {
                        "lat": float(row["gps_lat"]),
                        "lng": float(row["gps_lng"]),
                        "clat": float(row["center_lat"]),
                        "clng": float(row["center_lng"]),
                        "m": int(row["geofence_radius_m"]),
                    },
                )
                .mappings()
                .first()["ok"]
            )

    db.execute(text("update photos set within_geofence = :w where id = :id"), {"w": within, "id": str(UUID(payload.photo_id))})
    db.commit()
    return {"ok": True, "within_geofence": within}

