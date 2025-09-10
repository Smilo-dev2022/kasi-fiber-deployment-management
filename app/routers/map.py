from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.deps import get_db


router = APIRouter(prefix="/map", tags=["map"])


@router.get("/tiles")
def get_style_json(tile_url: Optional[str] = Query(None)):
    # Minimal MapLibre style; caller can override tiles with tokenized URL
    tiles = tile_url or "https://api.maptiler.com/tiles/v3/{z}/{x}/{y}.pbf?key={key}"
    return {
        "version": 8,
        "sources": {
            "osm": {
                "type": "vector",
                "tiles": [tiles],
                "minzoom": 0,
                "maxzoom": 14,
            }
        },
        "layers": [
            {"id": "background", "type": "background", "paint": {"background-color": "#ffffff"}}
        ],
    }


@router.get("/wards")
def wards_geojson(db: Session = Depends(get_db), bbox: Optional[str] = Query(None)):
    if bbox:
        minx, miny, maxx, maxy = [float(x) for x in bbox.split(",")]
        sql = text(
            """
            select json_build_object(
              'type','FeatureCollection',
              'features', coalesce(json_agg(json_build_object(
                'type','Feature',
                'id', id,
                'properties', json_build_object('name', name),
                'geometry', ST_AsGeoJSON(geom)::json
              )), '[]'::json)
            ) as fc
            from (select id, name, geom from geo_wards where geom && ST_MakeEnvelope(:minx,:miny,:maxx,:maxy, 4326)) q
            """
        )
        row = db.execute(sql, {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}).first()
    else:
        row = db.execute(
            text(
                """
                select json_build_object(
                  'type','FeatureCollection',
                  'features', coalesce(json_agg(json_build_object(
                    'type','Feature',
                    'id', id,
                    'properties', json_build_object('name', name),
                    'geometry', ST_AsGeoJSON(geom)::json
                  )), '[]'::json)
                ) as fc
                from geo_wards
                """
            )
        ).first()
    return row.fc if row else {"type": "FeatureCollection", "features": []}


@router.get("/pon/{pon_id}/assets")
def pon_assets_geojson(pon_id: str, db: Session = Depends(get_db)):
    sql = text(
        """
        with
        poles as (
          select id, code, 'pole' as type, geom from poles where pon_id = :pon
        ),
        closures as (
          select id, code, 'closure' as type, geom from splice_closures where pon_id = :pon and geom is not null
        ),
        splitters as (
          select id, code, 'splitter' as type, geom from splitters where pon_id = :pon and geom is not null
        ),
        cables as (
          select id, cable_code as code, 'cable' as type, geom from cable_register where pon_id = :pon and geom is not null
        ),
        points as (
          select * from poles
          union all select * from closures
          union all select * from splitters
        )
        select json_build_object(
          'type','FeatureCollection',
          'features', (
            coalesce((
              select json_agg(json_build_object(
                'type','Feature', 'id', id, 'properties', json_build_object('type', type, 'code', code), 'geometry', ST_AsGeoJSON(geom)::json
              )) from points
            ), '[]'::json) || coalesce((
              select json_agg(json_build_object(
                'type','Feature', 'id', id, 'properties', json_build_object('type', type, 'code', code), 'geometry', ST_AsGeoJSON(geom)::json
              )) from cables
            ), '[]'::json)
          )
        ) as fc
        """
    )
    row = db.execute(sql, {"pon": pon_id}).first()
    return row.fc if row else {"type": "FeatureCollection", "features": []}


@router.get("/incidents")
def incidents_geojson(db: Session = Depends(get_db), bbox: Optional[str] = Query(None), since: Optional[str] = Query(None)):
    params: dict = {}
    where = []
    if bbox:
        minx, miny, maxx, maxy = [float(x) for x in bbox.split(",")]
        where.append("geom && ST_MakeEnvelope(:minx,:miny,:maxx,:maxy,4326)")
        params.update({"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})
    if since:
        where.append("opened_at >= :since")
        params["since"] = since
    wsql = (" where " + " and ".join(where)) if where else ""
    row = db.execute(
        text(
            f"""
            select json_build_object(
              'type','FeatureCollection',
              'features', coalesce(json_agg(json_build_object(
                'type','Feature',
                'id', id,
                'properties', json_build_object('severity', severity, 'category', category, 'status', status, 'title', title),
                'geometry', ST_AsGeoJSON(geom)::json
              )), '[]'::json)
            ) as fc
            from (select id, severity, category, status, title, geom from incidents{wsql}) q
            """
        ),
        params,
    ).first()
    return row.fc if row else {"type": "FeatureCollection", "features": []}

