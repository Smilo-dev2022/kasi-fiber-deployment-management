from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.deps import get_db, require_roles
from app.models.fiber import (
    SpliceClosure,
    SpliceTray,
    Splice,
    FloatingRun,
    TestPlan,
    OTDRResult,
    LSPMResult,
    ConnectorInspect,
    CableRegister,
    TestPhoto,
)
from app.schemas.fiber import (
    SpliceClosureIn,
    SpliceClosureOut,
    SpliceTrayIn,
    SpliceTrayOut,
    SpliceIn,
    SpliceOut,
    FloatingRunIn,
    FloatingRunOut,
    FloatingRunCompleteIn,
    TestPlanIn,
    TestPlanOut,
    OTDRResultIn,
    OTDRResultOut,
    LSPMResultIn,
    LSPMResultOut,
    ConnectorInspectIn,
    ConnectorInspectOut,
    CableRegisterIn,
    CableRegisterOut,
    CableInstalledUpdate,
    TestPhotoIn,
    TestPhotoOut,
)
from app.services.exif import parse_exif
from app.services.s3 import put_bytes, get_object_bytes


router = APIRouter(prefix="", tags=["fiber"])


# /floating
floating = APIRouter(prefix="/floating", tags=["floating"])


@floating.post("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_floating(payload: FloatingRunIn, db: Session = Depends(get_db)):
    fr = FloatingRun(**payload.dict())
    db.add(fr)
    db.commit()
    return {"ok": True, "id": str(fr.id)}


@floating.patch("/{run_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def complete_floating(run_id: str, payload: FloatingRunCompleteIn, db: Session = Depends(get_db)):
    fr = db.get(FloatingRun, UUID(run_id))
    if not fr:
        raise HTTPException(404, "Not found")
    fr.meters = payload.meters
    fr.end_ts = datetime.fromisoformat(payload.end_ts) if payload.end_ts else datetime.now(timezone.utc)
    fr.photos_ok = payload.photos_ok
    # Variance check against planned segment length if available
    if fr.segment_id and fr.meters is not None:
        row = db.execute(text("select length_m from trench_segments where id=:id"), {"id": fr.segment_id}).first()
        if row and row[0] is not None:
            planned = float(row[0])
            actual = float(fr.meters)
            if planned > 0:
                variance = abs(actual - planned) / planned
                if variance > 0.05:
                    fr.passed = False
    if payload.passed is not None:
        fr.passed = payload.passed
    db.commit()
    return {"ok": True}


router.include_router(floating)


# /closures
closures = APIRouter(prefix="/closures", tags=["closures"])


@closures.post("", response_model=SpliceClosureOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def create_closure(payload: SpliceClosureIn, db: Session = Depends(get_db)):
    rec = SpliceClosure(**payload.dict())
    db.add(rec)
    db.commit()
    return SpliceClosureOut(id=str(rec.id), **payload.dict())


@closures.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_closures(pon_id: str, db: Session = Depends(get_db)):
    rows = db.query(SpliceClosure).filter(SpliceClosure.pon_id == UUID(pon_id)).all()
    return [
        {
            "id": str(r.id),
            "pon_id": str(r.pon_id),
            "code": r.code,
            "gps_lat": float(r.gps_lat) if r.gps_lat is not None else None,
            "gps_lng": float(r.gps_lng) if r.gps_lng is not None else None,
            "enclosure_type": r.enclosure_type,
            "tray_count": r.tray_count,
            "status": r.status,
        }
        for r in rows
    ]


@closures.patch("/{closure_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def update_closure(closure_id: str, tray_count: int | None = None, status: str | None = None, db: Session = Depends(get_db)):
    rec = db.get(SpliceClosure, UUID(closure_id))
    if not rec:
        raise HTTPException(404, "Not found")
    if tray_count is not None:
        rec.tray_count = tray_count
    if status is not None:
        rec.status = status
    db.commit()
    return {"ok": True}


router.include_router(closures)


# /closures/{id}/trays
trays = APIRouter(prefix="/closures/{closure_id}/trays", tags=["trays"])


@trays.post("", response_model=SpliceTrayOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def add_tray(closure_id: str, payload: SpliceTrayIn, db: Session = Depends(get_db)):
    if str(payload.closure_id) != closure_id:
        raise HTTPException(400, "closure_id mismatch")
    rec = SpliceTray(**payload.dict())
    db.add(rec)
    db.commit()
    return SpliceTrayOut(id=str(rec.id), splices_done=rec.splices_done, **payload.dict())


@trays.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_trays(closure_id: str, db: Session = Depends(get_db)):
    rows = db.query(SpliceTray).filter(SpliceTray.closure_id == UUID(closure_id)).all()
    return [
        {
            "id": str(r.id),
            "closure_id": str(r.closure_id),
            "tray_no": r.tray_no,
            "fiber_start": r.fiber_start,
            "fiber_end": r.fiber_end,
            "splices_planned": r.splices_planned,
            "splices_done": r.splices_done,
        }
        for r in rows
    ]


router.include_router(trays)


# /splices
splices = APIRouter(prefix="/splices", tags=["splices"])


@splices.post("", response_model=SpliceOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def record_splice(payload: SpliceIn, db: Session = Depends(get_db)):
    # Validation: splice loss thresholds; pass flag set based on rule unless waiver logic comes later
    passed = True
    if payload.loss_db is not None:
        passed = payload.loss_db <= 0.2
    rec = Splice(passed=passed, **payload.dict())
    db.add(rec)
    # update tray splices_done
    db.execute(text("update splice_trays set splices_done = splices_done + 1 where id = :id"), {"id": payload.tray_id})
    db.commit()
    return SpliceOut(id=str(rec.id), passed=rec.passed, **payload.dict())


@splices.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_splices(tray_id: str, db: Session = Depends(get_db)):
    rows = db.query(Splice).filter(Splice.tray_id == UUID(tray_id)).all()
    return [
        {
            "id": str(r.id),
            "tray_id": str(r.tray_id),
            "core": r.core,
            "from_cable": r.from_cable,
            "to_cable": r.to_cable,
            "loss_db": float(r.loss_db) if r.loss_db is not None else None,
            "method": r.method,
            "tech_id": str(r.tech_id) if r.tech_id else None,
            "time": r.time.isoformat() if r.time else None,
            "passed": r.passed,
        }
        for r in rows
    ]


@splices.patch("/{splice_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def update_splice(splice_id: str, loss_db: float | None = None, passed: bool | None = None, db: Session = Depends(get_db)):
    rec = db.get(Splice, UUID(splice_id))
    if not rec:
        raise HTTPException(404, "Not found")
    if loss_db is not None:
        rec.loss_db = loss_db
        rec.passed = loss_db <= 0.2 if passed is None else passed
    elif passed is not None:
        rec.passed = passed
    db.commit()
    return {"ok": True}


router.include_router(splices)


# /tests/plans
plans = APIRouter(prefix="/tests/plans", tags=["tests"])


@plans.post("", response_model=TestPlanOut, dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_plan(payload: TestPlanIn, db: Session = Depends(get_db)):
    rec = TestPlan(**payload.dict())
    db.add(rec)
    db.commit()
    return TestPlanOut(id=str(rec.id), **payload.dict())


@plans.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_plans(pon_id: str, db: Session = Depends(get_db)):
    rows = db.query(TestPlan).filter(TestPlan.pon_id == UUID(pon_id)).all()
    return [
        {
            "id": str(r.id),
            "pon_id": str(r.pon_id),
            "link_name": r.link_name,
            "from_point": r.from_point,
            "to_point": r.to_point,
            "wavelength_nm": r.wavelength_nm,
            "max_loss_db": float(r.max_loss_db),
            "otdr_required": r.otdr_required,
            "lspm_required": r.lspm_required,
        }
        for r in rows
    ]


router.include_router(plans)


# /tests/otdr
otdr = APIRouter(prefix="/tests/otdr", tags=["tests"])


@otdr.post("", response_model=OTDRResultOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def record_otdr(payload: OTDRResultIn, db: Session = Depends(get_db)):
    # Basic pass based on total/back-reflection where provided
    passed = True
    if payload.total_loss_db is not None:
        plan = db.get(TestPlan, UUID(payload.test_plan_id))
        if plan and plan.max_loss_db is not None:
            passed = float(payload.total_loss_db) <= float(plan.max_loss_db)
    # Back reflection spec (fail if worse than -35 dB)
    if passed and payload.back_reflection_db is not None:
        try:
            passed = float(payload.back_reflection_db) <= -35.0
        except Exception:
            passed = False
    rec = OTDRResult(passed=passed, **payload.dict())
    db.add(rec)
    db.commit()
    return OTDRResultOut(id=str(rec.id), passed=rec.passed, **payload.dict())


@otdr.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_otdr(test_plan_id: str, db: Session = Depends(get_db)):
    rows = db.query(OTDRResult).filter(OTDRResult.test_plan_id == UUID(test_plan_id)).all()
    return [
        {
            "id": str(r.id),
            "test_plan_id": str(r.test_plan_id),
            "file_url": r.file_url,
            "vendor": r.vendor,
            "wavelength_nm": r.wavelength_nm,
            "total_loss_db": float(r.total_loss_db) if r.total_loss_db is not None else None,
            "event_count": r.event_count,
            "max_splice_loss_db": float(r.max_splice_loss_db) if r.max_splice_loss_db is not None else None,
            "back_reflection_db": float(r.back_reflection_db) if r.back_reflection_db is not None else None,
            "tested_at": r.tested_at.isoformat() if r.tested_at else None,
            "passed": r.passed,
        }
        for r in rows
    ]


router.include_router(otdr)


# /tests/lspm
lspm = APIRouter(prefix="/tests/lspm", tags=["tests"])


@lspm.post("", response_model=LSPMResultOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def record_lspm(payload: LSPMResultIn, db: Session = Depends(get_db)):
    # Pass rule: measured_loss_db <= plan.max_loss_db
    plan = db.get(TestPlan, UUID(payload.test_plan_id))
    if not plan:
        raise HTTPException(400, "Invalid plan")
    passed = float(payload.measured_loss_db) <= float(plan.max_loss_db)
    margin_db = float(plan.max_loss_db) - float(payload.measured_loss_db)
    rec = LSPMResult(passed=passed, margin_db=margin_db, **payload.dict())
    db.add(rec)
    db.commit()
    return LSPMResultOut(id=str(rec.id), passed=rec.passed, **{**payload.dict(), "margin_db": margin_db})


@lspm.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_lspm(test_plan_id: str, db: Session = Depends(get_db)):
    rows = db.query(LSPMResult).filter(LSPMResult.test_plan_id == UUID(test_plan_id)).all()
    return [
        {
            "id": str(r.id),
            "test_plan_id": str(r.test_plan_id),
            "wavelength_nm": r.wavelength_nm,
            "measured_loss_db": float(r.measured_loss_db),
            "margin_db": float(r.margin_db) if r.margin_db is not None else None,
            "tested_at": r.tested_at.isoformat() if r.tested_at else None,
            "passed": r.passed,
        }
        for r in rows
    ]


router.include_router(lspm)


# /inspect
inspect = APIRouter(prefix="/inspect", tags=["inspect"])


@inspect.post("", response_model=ConnectorInspectOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def record_inspect(payload: ConnectorInspectIn, db: Session = Depends(get_db)):
    # Pass rule: grade must be A or B after cleaning
    passed = False
    if payload.cleaned and payload.retest_grade:
        passed = payload.retest_grade in ("A", "B")
    elif payload.grade:
        passed = payload.grade in ("A", "B")
    rec = ConnectorInspect(passed=passed, **payload.dict())
    db.add(rec)
    db.commit()
    return ConnectorInspectOut(id=str(rec.id), passed=rec.passed, **payload.dict())


@inspect.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_inspects(closure_id: str | None = None, device_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(ConnectorInspect)
    if closure_id:
        q = q.filter(ConnectorInspect.closure_id == UUID(closure_id))
    if device_id:
        q = q.filter(ConnectorInspect.device_id == UUID(device_id))
    rows = q.all()
    return [
        {
            "id": str(r.id),
            "closure_id": str(r.closure_id) if r.closure_id else None,
            "device_id": str(r.device_id) if r.device_id else None,
            "port": r.port,
            "microscope_photo_url": r.microscope_photo_url,
            "grade": r.grade,
            "cleaned": r.cleaned,
            "retest_grade": r.retest_grade,
            "tested_at": r.tested_at.isoformat() if r.tested_at else None,
            "passed": r.passed,
        }
        for r in rows
    ]


router.include_router(inspect)


# /cables
cables = APIRouter(prefix="/cables", tags=["cables"])


@cables.post("", response_model=CableRegisterOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def register_cable(payload: CableRegisterIn, db: Session = Depends(get_db)):
    rec = CableRegister(**payload.dict())
    db.add(rec)
    db.commit()
    return CableRegisterOut(id=str(rec.id), installed_m=rec.installed_m, **payload.dict())


@cables.patch("/{cable_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def update_installed(cable_id: str, payload: CableInstalledUpdate, db: Session = Depends(get_db)):
    rec = db.get(CableRegister, UUID(cable_id))
    if not rec:
        raise HTTPException(404, "Not found")
    rec.installed_m = payload.installed_m
    db.commit()
    return {"ok": True}


@cables.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def list_cables(pon_id: str, db: Session = Depends(get_db)):
    rows = db.query(CableRegister).filter(CableRegister.pon_id == UUID(pon_id)).all()
    return [
        {
            "id": str(r.id),
            "pon_id": str(r.pon_id),
            "cable_code": r.cable_code,
            "type": r.type,
            "length_m": r.length_m,
            "drum_code": r.drum_code,
            "installed_m": r.installed_m,
        }
        for r in rows
    ]


router.include_router(cables)


# /test-photos
tphotos = APIRouter(prefix="/test-photos", tags=["test-photos"])


@tphotos.post("", response_model=TestPhotoOut, dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def register_test_photo(payload: TestPhotoIn, db: Session = Depends(get_db)):
    rec = TestPhoto(**payload.dict(), exif_ok=False, within_geofence=False)
    db.add(rec)
    db.commit()
    return TestPhotoOut(id=str(rec.id), exif_ok=False, within_geofence=False, **payload.dict())


@tphotos.post("/validate", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def validate_test_photo(photo_id: str, db: Session = Depends(get_db)):
    rec = db.get(TestPhoto, UUID(photo_id))
    if not rec:
        raise HTTPException(404, "Not found")
    # For geofence, we need PON center; infer by entity if possible (closure->pon, else skip)
    exif_ok = rec.taken_ts is not None
    within_geofence = False
    # Attempt join to find PON center
    pon_row = db.execute(
        text(
            """
        select p.center_lat, p.center_lng, p.geofence_radius_m
        from pons p
        join splice_closures sc on sc.pon_id = p.id
        where :etype='SpliceClosure' and sc.id = :eid
        """
        ),
        {"etype": rec.entity_type, "eid": rec.entity_id},
    ).first()
    if pon_row and rec.gps_lat is not None and rec.gps_lng is not None:
        # Haversine inline
        from math import radians, sin, cos, asin, sqrt

        R = 6371000.0
        a_lat = float(rec.gps_lat)
        a_lng = float(rec.gps_lng)
        b_lat = float(pon_row[0])
        b_lng = float(pon_row[1])
        phi1 = radians(a_lat)
        phi2 = radians(b_lat)
        dphi = radians(b_lat - a_lat)
        dlmb = radians(b_lng - a_lng)
        h = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
        dist = 2 * R * asin(sqrt(h))
        within_geofence = dist <= float(pon_row[2])
    rec.exif_ok = exif_ok
    rec.within_geofence = within_geofence
    db.commit()
    return {"ok": True, "exif_ok": exif_ok, "within_geofence": within_geofence}


router.include_router(tphotos)


# Importers
imports = APIRouter(prefix="/tests", tags=["tests-import"])


@imports.post("/otdr/import", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def import_otdr(
    file: UploadFile = File(...),
    test_plan_id: str | None = Form(default=None),
    link_name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    content = file.file.read()
    ext = (file.filename.split(".")[-1] or "").lower()
    key = f"otdr/imports/{uuid4()}.{ext}"
    url = put_bytes(key, file.content_type or "application/octet-stream", content)

    plan = None
    if test_plan_id:
        plan = db.get(TestPlan, UUID(test_plan_id))
    elif link_name:
        plan = db.query(TestPlan).filter(TestPlan.link_name == link_name).first()
    if not plan:
        raise HTTPException(400, "Test plan not found")

    metrics = {"vendor": None, "wavelength_nm": None, "total_loss_db": None, "event_count": None, "max_splice_loss_db": None, "back_reflection_db": None}
    if ext == "csv":
        try:
            import csv, io

            text_io = io.StringIO(content.decode("utf-8", errors="ignore"))
            reader = csv.DictReader(text_io)
            for row in reader:
                # pick first
                metrics["vendor"] = row.get("vendor") or row.get("Vendor")
                metrics["wavelength_nm"] = int(row.get("wavelength_nm") or row.get("Wavelength") or 1310)
                metrics["total_loss_db"] = float(row.get("total_loss_db") or row.get("TotalLoss") or 0)
                metrics["event_count"] = int(row.get("event_count") or row.get("Events") or 0)
                metrics["max_splice_loss_db"] = float(row.get("max_splice_loss_db") or row.get("MaxSpliceLoss") or 0)
                br = row.get("back_reflection_db") or row.get("BackReflection")
                metrics["back_reflection_db"] = float(br) if br not in (None, "") else None
                break
        except Exception:
            pass
    # .sor and others: keep URL only
    passed = True
    if metrics["total_loss_db"] is not None and plan.max_loss_db is not None:
        passed = float(metrics["total_loss_db"]) <= float(plan.max_loss_db)
    if passed and metrics["back_reflection_db"] is not None:
        try:
            passed = float(metrics["back_reflection_db"]) <= -35.0
        except Exception:
            passed = False
    rec = OTDRResult(
        test_plan_id=plan.id,
        file_url=url,
        vendor=metrics["vendor"],
        wavelength_nm=metrics["wavelength_nm"] or int(plan.wavelength_nm),
        total_loss_db=metrics["total_loss_db"],
        event_count=metrics["event_count"],
        max_splice_loss_db=metrics["max_splice_loss_db"],
        back_reflection_db=metrics["back_reflection_db"],
        tested_at=datetime.now(timezone.utc),
        passed=passed,
    )
    db.add(rec)
    db.commit()
    return {"ok": True, "id": str(rec.id), "url": url, "passed": passed}


@imports.post("/lspm/import", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def import_lspm(
    file: UploadFile = File(...),
    pon_id: str = Form(...),
    db: Session = Depends(get_db),
):
    content = file.file.read()
    ext = (file.filename.split(".")[-1] or "").lower()
    if ext != "csv":
        raise HTTPException(400, "CSV required")
    import csv, io

    text_io = io.StringIO(content.decode("utf-8", errors="ignore"))
    reader = csv.DictReader(text_io)
    imported = 0
    for row in reader:
        try:
            link_name = row.get("link_name") or row.get("Link")
            wl = int(row.get("wavelength") or row.get("Wavelength") or 1310)
            loss = float(row.get("loss_db") or row.get("Loss") or 0)
            plan = db.query(TestPlan).filter(TestPlan.pon_id == UUID(pon_id), TestPlan.link_name == link_name, TestPlan.wavelength_nm == wl).first()
            if not plan:
                continue
            passed = float(loss) <= float(plan.max_loss_db)
            margin = float(plan.max_loss_db) - float(loss)
            rec = LSPMResult(test_plan_id=plan.id, wavelength_nm=wl, measured_loss_db=loss, margin_db=margin, tested_at=datetime.now(timezone.utc), passed=passed)
            db.add(rec)
            imported += 1
        except Exception:
            continue
    db.commit()
    return {"ok": True, "imported": imported}


@tphotos.post("/validate-upload", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
def validate_test_photo_upload(photo_id: str = Form(...), s3_key: str = Form(...), db: Session = Depends(get_db)):
    rec = db.get(TestPhoto, UUID(photo_id))
    if not rec:
        raise HTTPException(404, "Not found")
    blob = get_object_bytes(s3_key)
    meta = parse_exif(blob)
    rec.taken_ts = meta.get("taken_ts")
    rec.gps_lat = meta.get("gps_lat")
    rec.gps_lng = meta.get("gps_lng")
    # Reuse validation
    _ = validate_test_photo(photo_id=str(rec.id), db=db)
    return {"ok": True, "exif_ok": rec.exif_ok, "within_geofence": rec.within_geofence}


router.include_router(imports)

