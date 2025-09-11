from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import json

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/geojson", dependencies=[Depends(require_roles("ADMIN", "PM"))])
async def import_geojson(
    layer: str = Form(..., description="one of: wards, suburbs, poles, closures, cables"),
    pon_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        data = json.loads((await file.read()).decode("utf-8"))
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    if data.get("type") != "FeatureCollection":
        raise HTTPException(400, "Expected GeoJSON FeatureCollection")

    count = 0
    if layer == "wards":
        for f in data.get("features", []):
            name = f.get("properties", {}).get("name") or f.get("properties", {}).get("WARD_NAME")
            code = f.get("properties", {}).get("code") or f.get("properties", {}).get("WARD_NO")
            geom = json.dumps(f.get("geometry"))
            db.execute(text("insert into geo_wards (id, name, code, geom) values (gen_random_uuid(), :n, :c, ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326))"), {"n": name, "c": code, "g": geom})
            count += 1
    elif layer == "suburbs":
        for f in data.get("features", []):
            name = f.get("properties", {}).get("name") or f.get("properties", {}).get("SUB_PLACE")
            ward_id = f.get("properties", {}).get("ward_id")
            geom = json.dumps(f.get("geometry"))
            db.execute(text("insert into geo_suburbs (id, name, ward_id, geom) values (gen_random_uuid(), :n, :w, ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326))"), {"n": name, "w": ward_id, "g": geom})
            count += 1
    elif layer == "closures":
        if not pon_id:
            raise HTTPException(400, "pon_id required for closures import")
        for f in data.get("features", []):
            code = f.get("properties", {}).get("code")
            geom = json.dumps(f.get("geometry"))
            db.execute(text("insert into splice_closures (id, pon_id, code, geom, status) values (gen_random_uuid(), :p, :c, ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326), 'Planned') on conflict (code) do update set geom = excluded.geom"), {"p": pon_id, "c": code, "g": geom})
            count += 1
    elif layer == "poles":
        if not pon_id:
            raise HTTPException(400, "pon_id required for poles import")
        for f in data.get("features", []):
            code = f.get("properties", {}).get("code")
            geom = json.dumps(f.get("geometry"))
            db.execute(text("insert into poles (id, pon_id, code, geom, status) values (gen_random_uuid(), :p, :c, ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326), 'Planned')"), {"p": pon_id, "c": code, "g": geom})
            count += 1
    elif layer == "cables":
        if not pon_id:
            raise HTTPException(400, "pon_id required for cables import")
        for f in data.get("features", []):
            code = f.get("properties", {}).get("cable_code") or f.get("properties", {}).get("code")
            cable_type = f.get("properties", {}).get("type") or "trench"
            chainage = f.get("properties", {}).get("chainage_m")
            geom = json.dumps(f.get("geometry"))
            db.execute(text("insert into cable_register (id, pon_id, cable_code, type, chainage_m, geom) values (gen_random_uuid(), :p, :c, :t, :m, ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326)) on conflict do nothing"), {"p": pon_id, "c": code, "t": cable_type, "m": chainage, "g": geom})
            count += 1
    else:
        raise HTTPException(400, "Unsupported layer")

    db.commit()
    return {"ok": True, "imported": count}

