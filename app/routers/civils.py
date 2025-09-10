from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from app.core.deps import get_db, require_roles
from app.models.civils import TrenchSegment, DuctInstall, Reinstatement, CivilsPhoto
from app.models.pon import PON


router = APIRouter(prefix="/civils", tags=["civils"])


class SegmentIn(BaseModel):
    pon_id: str
    start_gps: Optional[str] = None
    end_gps: Optional[str] = None
    length_m: Optional[float] = None
    width_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    surface_type: Optional[str] = None
    path_geojson: Optional[str] = None


class AssignIn(BaseModel):
    assigned_team: str


class StatusIn(BaseModel):
    status: Literal["Planned", "Opened", "DuctLaid", "Backfilled", "Reinstated", "Snag"]


class PathIn(BaseModel):
    path_geojson: str


@router.post("/trench-segments", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_segment(payload: SegmentIn, db: Session = Depends(get_db)):
    seg = TrenchSegment(
        id=uuid4(),
        pon_id=UUID(payload.pon_id),
        start_gps=payload.start_gps,
        end_gps=payload.end_gps,
        length_m=payload.length_m,
        width_mm=payload.width_mm,
        depth_mm=payload.depth_mm,
        surface_type=payload.surface_type,
        path_geojson=payload.path_geojson,
    )
    db.add(seg)
    db.commit()
    return {"ok": True, "id": str(seg.id)}


@router.get("/trench-segments")
def list_segments(pon_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(TrenchSegment)
    if pon_id:
        q = q.filter(TrenchSegment.pon_id == UUID(pon_id))
    rows = q.all()
    return [
        {
            "id": str(r.id),
            "pon_id": str(r.pon_id),
            "start_gps": r.start_gps,
            "end_gps": r.end_gps,
            "length_m": float(r.length_m) if r.length_m is not None else None,
            "width_mm": r.width_mm,
            "depth_mm": r.depth_mm,
            "surface_type": r.surface_type,
            "status": r.status,
            "assigned_team": r.assigned_team,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "path_geojson": r.path_geojson,
        }
        for r in rows
    ]


@router.get("/trench-segments/{segment_id}")
def get_segment(segment_id: str, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(segment_id))
    if not seg:
        raise HTTPException(404, "Not found")
    return {
        "id": str(seg.id),
        "pon_id": str(seg.pon_id),
        "start_gps": seg.start_gps,
        "end_gps": seg.end_gps,
        "length_m": float(seg.length_m) if seg.length_m is not None else None,
        "width_mm": seg.width_mm,
        "depth_mm": seg.depth_mm,
        "surface_type": seg.surface_type,
        "status": seg.status,
        "assigned_team": seg.assigned_team,
        "started_at": seg.started_at,
        "completed_at": seg.completed_at,
        "path_geojson": seg.path_geojson,
    }


class SegmentUpdate(BaseModel):
    start_gps: Optional[str] = None
    end_gps: Optional[str] = None
    length_m: Optional[float] = None
    width_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    surface_type: Optional[str] = None
    path_geojson: Optional[str] = None


@router.patch("/trench-segments/{segment_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def update_segment(segment_id: str, payload: SegmentUpdate, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(segment_id))
    if not seg:
        raise HTTPException(404, "Not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(seg, field, value)
    db.commit()
    return {"ok": True}


@router.delete("/trench-segments/{segment_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def delete_segment(segment_id: str, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(segment_id))
    if not seg:
        raise HTTPException(404, "Not found")
    db.delete(seg)
    db.commit()
    return {"ok": True}


@router.patch("/trench-segments/{segment_id}/assign", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def assign_team(segment_id: str, payload: AssignIn, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(segment_id))
    if not seg:
        raise HTTPException(404, "Not found")
    seg.assigned_team = payload.assigned_team
    db.commit()
    return {"ok": True}


@router.patch("/trench-segments/{segment_id}/status", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def set_status(segment_id: str, payload: StatusIn, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(segment_id))
    if not seg:
        raise HTTPException(404, "Not found")
    prev = seg.status
    seg.status = payload.status
    now = datetime.now(timezone.utc)
    if prev == "Planned" and payload.status == "Opened":
        seg.started_at = now
    if payload.status == "Reinstated":
        seg.completed_at = now
    db.commit()
    return {"ok": True}


@router.patch("/trench-segments/{segment_id}/path", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def set_path(segment_id: str, payload: PathIn, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(segment_id))
    if not seg:
        raise HTTPException(404, "Not found")
    seg.path_geojson = payload.path_geojson
    db.commit()
    return {"ok": True}


# Civils Photos


class CivilsPhotoIn(BaseModel):
    segment_id: str
    kind: Literal["MarkOut", "OpenTrench", "Bedding", "Duct", "WarningTape", "Backfill", "Reinstatement"]
    url: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    taken_ts: Optional[datetime] = None


def distance_m(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    import math

    R = 6371000.0
    phi1 = math.radians(a_lat)
    phi2 = math.radians(b_lat)
    dphi = math.radians(b_lat - a_lat)
    dlmb = math.radians(b_lng - a_lng)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


@router.post("/photos", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def add_civils_photo(payload: CivilsPhotoIn, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(payload.segment_id))
    if not seg:
        raise HTTPException(404, "Segment not found")
    row = CivilsPhoto(
        id=uuid4(),
        segment_id=seg.id,
        kind=payload.kind,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        taken_ts=payload.taken_ts,
        url=payload.url,
    )
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}


@router.get("/photos")
def list_civils_photos(segment_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(CivilsPhoto)
        .filter(CivilsPhoto.segment_id == UUID(segment_id))
        .order_by(CivilsPhoto.taken_ts.desc().nullslast())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "segment_id": str(r.segment_id),
            "kind": r.kind,
            "gps_lat": float(r.gps_lat) if r.gps_lat is not None else None,
            "gps_lng": float(r.gps_lng) if r.gps_lng is not None else None,
            "taken_ts": r.taken_ts,
            "exif_ok": r.exif_ok,
            "within_geofence": r.within_geofence,
            "url": r.url,
        }
        for r in rows
    ]


@router.post("/photos/{photo_id}/validate", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def validate_civils_photo(photo_id: str, db: Session = Depends(get_db)):
    p = db.get(CivilsPhoto, UUID(photo_id))
    if not p:
        raise HTTPException(404, "Not found")
    seg = db.get(TrenchSegment, p.segment_id)
    if not seg:
        raise HTTPException(404, "Segment not found")
    pon = db.get(PON, seg.pon_id)
    if not pon or not pon.center_lat or not pon.center_lng:
        raise HTTPException(400, "PON geofence missing")
    if not p.taken_ts:
        raise HTTPException(400, "Missing EXIF DateTime")
    p.exif_ok = abs((datetime.now(timezone.utc) - p.taken_ts)) <= timedelta(hours=24)
    if p.gps_lat is None or p.gps_lng is None:
        p.within_geofence = False
    else:
        p.within_geofence = (
            distance_m(
                float(p.gps_lat),
                float(p.gps_lng),
                float(pon.center_lat),
                float(pon.center_lng),
            )
            <= pon.geofence_radius_m
        )
    db.commit()
    return {"ok": True, "exif_ok": p.exif_ok, "within_geofence": p.within_geofence}


# Duct installs


class DuctInstallIn(BaseModel):
    segment_id: str
    duct_type: Literal["20mm", "32mm", "50mm", "110mm", "microduct bundle"]
    count: int = 1
    rope_drawn: bool = False


@router.post("/duct-installs", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def add_duct_install(payload: DuctInstallIn, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(payload.segment_id))
    if not seg:
        raise HTTPException(404, "Segment not found")
    row = DuctInstall(
        id=uuid4(),
        segment_id=seg.id,
        duct_type=payload.duct_type,
        count=payload.count,
        rope_drawn=payload.rope_drawn,
    )
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}


class MandrelIn(BaseModel):
    passed: bool


@router.patch("/duct-installs/{install_id}/mandrel", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def set_mandrel(install_id: str, payload: MandrelIn, db: Session = Depends(get_db)):
    row = db.get(DuctInstall, UUID(install_id))
    if not row:
        raise HTTPException(404, "Not found")
    row.mandrel_passed = payload.passed
    db.commit()
    return {"ok": True}


# Reinstatements


class ReinstatementIn(BaseModel):
    segment_id: str
    surface_type: str
    area_m2: Optional[float] = None
    method: Optional[str] = None


@router.post("/reinstatements", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def create_reinstatement(payload: ReinstatementIn, db: Session = Depends(get_db)):
    seg = db.get(TrenchSegment, UUID(payload.segment_id))
    if not seg:
        raise HTTPException(404, "Segment not found")
    row = Reinstatement(
        id=uuid4(),
        segment_id=seg.id,
        surface_type=payload.surface_type,
        area_m2=payload.area_m2,
        method=payload.method,
    )
    db.add(row)
    db.commit()
    return {"ok": True, "id": str(row.id)}


@router.patch("/reinstatements/{reinst_id}/pass", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def pass_reinstatement(reinst_id: str, db: Session = Depends(get_db)):
    row = db.get(Reinstatement, UUID(reinst_id))
    if not row:
        raise HTTPException(404, "Not found")
    row.passed = True
    db.commit()
    return {"ok": True}


class SignOffIn(BaseModel):
    signed_off_by: str


@router.patch("/reinstatements/{reinst_id}/sign-off", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def signoff_reinstatement(reinst_id: str, payload: SignOffIn, db: Session = Depends(get_db)):
    row = db.get(Reinstatement, UUID(reinst_id))
    if not row:
        raise HTTPException(404, "Not found")
    row.signed_off_by = payload.signed_off_by
    row.signed_off_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}

