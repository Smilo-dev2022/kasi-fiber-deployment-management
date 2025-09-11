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


class StatusIn(BaseModel):
    status: str


def _pon_tests_passed(db: Session, pon_id: str) -> bool:
    # A PON is considered test-passed when for every plan:
    #  - if otdr_required then an OTDR result with passed=true exists
    #  - if lspm_required then an LSPM result with passed=true exists
    sql = text(
        """
        with plans as (
          select id, otdr_required, lspm_required from test_plans where pon_id = :p
        ), otdr_ok as (
          select tp.id as plan_id, exists (
            select 1 from otdr_results orr where orr.test_plan_id = tp.id and orr.passed = true
          ) as ok
          from plans tp
        ), lspm_ok as (
          select tp.id as plan_id, exists (
            select 1 from lspm_results lrr where lrr.test_plan_id = tp.id and lrr.passed = true
          ) as ok
          from plans tp
        )
        select coalesce(bool_and(case when p.otdr_required then o.ok else true end) 
                      and bool_and(case when p.lspm_required then l.ok else true end), true) as all_ok
        from plans p
        left join otdr_ok o on o.plan_id = p.id
        left join lspm_ok l on l.plan_id = p.id
        """
    )
    row = db.execute(sql, {"p": pon_id}).mappings().first()
    return bool(row and row["all_ok"]) if row is not None else True


@router.patch("/{pon_id}/status", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def set_status(pon_id: str, payload: StatusIn, db: Session = Depends(get_db)):
    # If moving to Completed or ReadyForInvoice, enforce test plan checks
    target = (payload.status or "").strip()
    if target in ("Completed", "ReadyForInvoice"):
        if not _pon_tests_passed(db, pon_id):
            raise HTTPException(400, "OTDR/LSPM requirements not met for Test Plan")
    db.execute(text("update pons set status = :s where id = :id"), {"s": target, "id": pon_id})
    db.commit()
    return {"ok": True, "status": target}

