from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.deps import get_db, require_roles
from app.models.pon import PON
from sqlalchemy import text
import json
from uuid import uuid4, UUID


router = APIRouter(prefix="/pons", tags=["pons"])


class GeoIn(BaseModel):
    center_lat: float
    center_lng: float
    geofence_radius_m: int = 200


@router.post("/{pon_id}/geofence", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def set_geofence(pon_id: str, payload: GeoIn, db: Session = Depends(get_db)):
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


@router.patch("/{pon_id}/geofence", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def patch_geofence_polygon(pon_id: str, payload: dict, db: Session = Depends(get_db)):
    """Compatibility endpoint: accepts either {"geometry": GeoJSON} or a raw GeoJSON object.
    """
    # Determine geometry payload
    gjson = payload.get("geometry") if isinstance(payload, dict) else None
    if not gjson and isinstance(payload, dict) and payload.get("type") in ("Polygon", "MultiPolygon"):
        gjson = payload
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


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def list_pons(db: Session = Depends(get_db)):
    rows = (
        db.execute(text("select id::text as id, status, center_lat, center_lng, geofence_radius_m from pons order by id desc limit 50"))
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


class PONIn(BaseModel):
    name: str | None = None
    ward: str | None = None


@router.post("", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_pon(_: PONIn, db: Session = Depends(get_db)):
    pid = str(uuid4())
    db.execute(text("insert into pons (id, status) values (:id, 'planned')"), {"id": pid})
    db.commit()
    return {"ok": True, "id": pid}

