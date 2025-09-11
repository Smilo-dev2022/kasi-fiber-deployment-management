from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, Dict, List, Optional

from app.core.deps import get_db, require_roles


router = APIRouter(prefix="/map", tags=["map"])


@router.get("/tiles")
def get_style_json(token: Optional[str] = Query(None)) -> Dict[str, Any]:
    # Token is passed through to style URLs when needed
    style: Dict[str, Any] = {
        "version": 8,
        "name": "Base SA",
        "sources": {
            "basemap": {
                "type": "vector",
                "tiles": [
                    f"https://api.maptiler.com/tiles/v3/tiles.json?key={token or '{token}'}"
                ],
            }
        },
        "glyphs": f"https://api.maptiler.com/fonts/{{fontstack}}/{{range}}.pbf?key={token or '{token}'}",
        "sprite": f"https://api.maptiler.com/maps/streets/sprite?key={token or '{token}'}",
        "layers": [
            {"id": "background", "type": "background", "paint": {"background-color": "#f8f9fb"}},
        ],
    }
    return style


@router.get("/wards", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def wards_geojson(db: Session = Depends(get_db)) -> Dict[str, Any]:
    rows = (
        db.execute(text("select id, name, code, ST_AsGeoJSON(geom)::json as geom from geo_wards limit 2000"))
        .mappings()
        .all()
    )
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": str(r["id"]), "properties": {"name": r["name"], "code": r["code"]}, "geometry": r["geom"]}
            for r in rows
        ],
    }


@router.get("/pon/{pon_id}/assets", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def pon_assets_geojson(pon_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Closures
    closures = (
        db.execute(
            text(
                "select id, code, status, ST_AsGeoJSON(geom)::json as geom from splice_closures where pon_id = :p"
            ),
            {"p": pon_id},
        )
        .mappings()
        .all()
    )

    # Poles
    poles = (
        db.execute(
            text("select id, code, status, ST_AsGeoJSON(geom)::json as geom from poles where pon_id = :p"),
            {"p": pon_id},
        )
        .mappings()
        .all()
    )

    # Cables
    cables = (
        db.execute(
            text(
                "select id, cable_code, type, chainage_m, ST_AsGeoJSON(geom)::json as geom from cable_register where pon_id = :p and geom is not null"
            ),
            {"p": pon_id},
        )
        .mappings()
        .all()
    )

    feats: List[Dict[str, Any]] = []
    feats += [
        {
            "type": "Feature",
            "id": str(r["id"]),
            "properties": {"type": "closure", "code": r["code"], "status": r["status"]},
            "geometry": r["geom"],
        }
        for r in closures
        if r["geom"]
    ]
    feats += [
        {
            "type": "Feature",
            "id": str(r["id"]),
            "properties": {"type": "pole", "code": r["code"], "status": r["status"]},
            "geometry": r["geom"],
        }
        for r in poles
        if r["geom"]
    ]
    feats += [
        {
            "type": "Feature",
            "id": str(r["id"]),
            "properties": {"type": r["type"] or "trench", "code": r["cable_code"], "chainage_m": r["chainage_m"]},
            "geometry": r["geom"],
        }
        for r in cables
    ]

    return {"type": "FeatureCollection", "features": feats}


@router.get("/incidents", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "AUDITOR"))])
def incidents_geojson(
    bbox: Optional[str] = Query(None, description="minx,miny,maxx,maxy in lon,lat (WGS84)"),
    since: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    clauses: List[str] = []
    params: Dict[str, Any] = {}
    if bbox:
        # bbox is in lon/lat, WGS84
        clauses.append("ST_Intersects(geom, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326))")
        minx, miny, maxx, maxy = [float(x) for x in bbox.split(",")]
        params.update({"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})
    if since:
        clauses.append("coalesce(opened_at, created_at) >= :since")
        params["since"] = since
    where_sql = (" where " + " and ".join(clauses)) if clauses else ""
    rows = (
        db.execute(text(f"select id, category, severity, status, ST_AsGeoJSON(geom)::json as geom from incidents{where_sql} order by opened_at desc nulls last limit 2000"), params)
        .mappings()
        .all()
    )
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "id": str(r["id"]), "properties": {"category": r["category"], "severity": r["severity"], "status": r["status"]}, "geometry": r["geom"]}
            for r in rows
            if r["geom"]
        ],
    }

