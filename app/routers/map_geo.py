from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional
from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/map", tags=["map"])


def _fc(features):  # FeatureCollection
    return {"type": "FeatureCollection", "features": features}


@router.get("/wards", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "AUDITOR", "SITE"))])
def wards(db: Session = Depends(get_db)):
    # Expect geo_wards.geom stored as WKB; convert in SQL
    rows = (
        db.execute(
            text(
                """
      SELECT id, name, ST_AsGeoJSON(public.ST_GeomFromWKB(geom)) AS gj FROM geo_wards
    """
            )
        )
        .mappings()
        .all()
    )
    feats = [
        {
            "type": "Feature",
            "id": r["id"],
            "properties": {"name": r["name"]},
            "geometry": r["gj"] and __import__("json").loads(r["gj"]),
        }
        for r in rows
    ]
    return _fc(feats)


@router.get("/pon/{pon_id}/assets", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "AUDITOR", "SITE"))])
def pon_assets(pon_id: str, db: Session = Depends(get_db)):
    feats = []
    # PON geofence
    g = db.execute(text("SELECT geofence FROM pons WHERE id=:p"), {"p": pon_id}).scalar()
    if g:
        feats.append({"type": "Feature", "properties": {"type": "geofence"}, "geometry": g})
    # Poles
    try:
        rows = (
            db.execute(
                text(
                    """
      SELECT id, code, geom_geojson FROM poles WHERE pon_id=:p AND geom_geojson IS NOT NULL
    """
                ),
                {"p": pon_id},
            )
            .mappings()
            .all()
        )
        feats += [
            {
                "type": "Feature",
                "properties": {"type": "pole", "id": str(r["id"]), "code": r["code"]},
                "geometry": r["geom_geojson"],
            }
            for r in rows
        ]
    except Exception:
        pass
    # Closures
    try:
        rows = (
            db.execute(
                text(
                    """
      SELECT id, code, geom_geojson FROM splice_closures WHERE pon_id=:p AND geom_geojson IS NOT NULL
    """
                ),
                {"p": pon_id},
            )
            .mappings()
            .all()
        )
        feats += [
            {
                "type": "Feature",
                "properties": {"type": "closure", "id": str(r["id"]), "code": r["code"]},
                "geometry": r["geom_geojson"],
            }
            for r in rows
        ]
    except Exception:
        pass
    # Cables
    try:
        rows = (
            db.execute(
                text(
                    """
      SELECT id, type, geom_geojson FROM cable_register WHERE pon_id=:p AND geom_geojson IS NOT NULL
    """
                ),
                {"p": pon_id},
            )
            .mappings()
            .all()
        )
        feats += [
            {
                "type": "Feature",
                "properties": {"type": "cable", "id": str(r["id"]), "cable_type": r["type"]},
                "geometry": r["geom_geojson"],
            }
            for r in rows
        ]
    except Exception:
        pass
    return _fc(feats)


@router.get("/incidents", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC", "AUDITOR"))])
def incidents(
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    since_minutes: int = Query(1440),
    db: Session = Depends(get_db),
):
    where = [
        "i.geom_geojson IS NOT NULL",
        "i.status IN ('Open','Acknowledged')",
        "i.opened_at >= :since",
    ]
    params = {"since": datetime.utcnow() - timedelta(minutes=since_minutes)}
    if bbox:
        try:
            minx, miny, maxx, maxy = [float(x) for x in bbox.split(",")]
        except Exception:
            raise HTTPException(400, "Invalid bbox")
        where.append("ST_Intersects(v.geom, ST_MakeEnvelope(:minx,:miny,:maxx,:maxy,4326))")
        params.update({"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})
    rows = (
        db.execute(
            text(
                f"""
      SELECT i.id, i.severity, i.category, i.title, ST_AsGeoJSON(v.geom) AS gj
      FROM v_incidents v
      JOIN incidents i ON i.id=v.id
      WHERE {" AND ".join(where)}
      ORDER BY i.opened_at DESC
      LIMIT 2000
    """
            ),
            params,
        )
        .mappings()
        .all()
    )
    feats = [
        {
            "type": "Feature",
            "properties": {
                "id": str(r["id"]),
                "severity": r["severity"],
                "category": r["category"],
                "title": r["title"],
            },
            "geometry": r["gj"] and __import__("json").loads(r["gj"]),
        }
        for r in rows
    ]
    return _fc(feats)

