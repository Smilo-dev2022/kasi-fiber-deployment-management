from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db, require_roles
from app.models.pon import PON
from sqlalchemy import text
import json


router = APIRouter(prefix="/pons", tags=["pons"])


class GeoIn(BaseModel):
    center_lat: float
    center_lng: float
    geofence_radius_m: int = 200


@router.post("/{pon_id}/geofence", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def set_geofence(pon_id: str, payload: GeoIn, db: Session = Depends(get_db)):
    from uuid import UUID

    pon = db.get(PON, UUID(pon_id))
    if not pon:
        raise HTTPException(404, "Not found")
    pon.center_lat = payload.center_lat
    pon.center_lng = payload.center_lng
    pon.geofence_radius_m = payload.geofence_radius_m
    db.commit()
    return {"ok": True}


class PolyIn(BaseModel):
    # GeoJSON Polygon or MultiPolygon
    geometry: dict


@router.post("/{pon_id}/geofence/polygon", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def set_geofence_polygon(pon_id: str, payload: PolyIn, db: Session = Depends(get_db)):
    from uuid import UUID

    gjson = payload.geometry
    if not isinstance(gjson, dict) or gjson.get("type") not in ("Polygon", "MultiPolygon"):
        raise HTTPException(400, "geometry must be Polygon or MultiPolygon")
    db.execute(
        text(
            "update pons set geofence_geom = ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326) where id = :id"
        ),
        {"g": json.dumps(gjson), "id": str(UUID(pon_id))},
    )
    db.commit()
    return {"ok": True}

