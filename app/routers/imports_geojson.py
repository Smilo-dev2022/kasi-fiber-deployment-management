from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/imports", tags=["imports"])


class ImportIn(BaseModel):
    kind: Literal["ward", "suburb", "poles", "closures", "cables"]
    geojson: dict


@router.post("/geojson", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def import_geojson(payload: ImportIn, db: Session = Depends(get_db)):
    gj = payload.geojson
    if gj.get("type") != "FeatureCollection":
        raise HTTPException(400, "Expected FeatureCollection")

    inserted = 0
    if payload.kind in ("ward", "suburb"):
        for feat in gj.get("features", []):
            name = (feat.get("properties") or {}).get("name") or "Unnamed"
            geom_json = feat.get("geometry")
            if not geom_json:
                continue
            if payload.kind == "ward":
                sql = text("insert into geo_wards (id, name, geom) values (gen_random_uuid(), :name, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)) on conflict do nothing")
                db.execute(sql, {"name": name, "geom": str(geom_json)})
            else:
                ward_id = (feat.get("properties") or {}).get("ward_id")
                sql = text("insert into geo_suburbs (id, name, ward_id, geom) values (gen_random_uuid(), :name, :ward_id, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)) on conflict do nothing")
                db.execute(sql, {"name": name, "ward_id": ward_id, "geom": str(geom_json)})
            inserted += 1
    elif payload.kind in ("poles", "closures"):
        table = "poles" if payload.kind == "poles" else "splice_closures"
        for feat in gj.get("features", []):
            props = feat.get("properties") or {}
            code = props.get("code")
            pon_id = props.get("pon_id")
            geom_json = feat.get("geometry")
            if not geom_json or not pon_id:
                continue
            if table == "poles":
                sql = text("insert into poles (id, pon_id, code, geom) values (gen_random_uuid(), :pon_id, :code, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)) on conflict (code) do nothing")
            else:
                sql = text("insert into splice_closures (id, pon_id, code, geom) values (gen_random_uuid(), :pon_id, :code, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)) on conflict (code) do nothing")
            db.execute(sql, {"pon_id": pon_id, "code": code, "geom": str(geom_json)})
            inserted += 1
    elif payload.kind == "cables":
        for feat in gj.get("features", []):
            props = feat.get("properties") or {}
            code = props.get("code") or props.get("cable_code")
            pon_id = props.get("pon_id")
            geom_json = feat.get("geometry")
            if not geom_json or not pon_id or not code:
                continue
            sql = text("insert into cable_register (id, pon_id, cable_code, geom) values (gen_random_uuid(), :pon_id, :code, ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)) on conflict do nothing")
            db.execute(sql, {"pon_id": pon_id, "code": code, "geom": str(geom_json)})
            inserted += 1

    db.commit()
    return {"ok": True, "inserted": inserted}

