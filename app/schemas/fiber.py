from pydantic import BaseModel, Field
from typing import Optional, Literal


class SpliceClosureIn(BaseModel):
    pon_id: str
    code: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    enclosure_type: Optional[str] = None
    tray_count: Optional[int] = None
    status: Optional[str] = None


class SpliceClosureOut(SpliceClosureIn):
    id: str


class SpliceTrayIn(BaseModel):
    closure_id: str
    tray_no: int
    fiber_start: Optional[int] = None
    fiber_end: Optional[int] = None
    splices_planned: Optional[int] = None


class SpliceTrayOut(SpliceTrayIn):
    id: str
    splices_done: int


class SpliceIn(BaseModel):
    tray_id: str
    core: int
    from_cable: Optional[str] = None
    to_cable: Optional[str] = None
    loss_db: Optional[float] = None
    method: Optional[Literal["fusion", "mechanical"]] = None
    tech_id: Optional[str] = None
    time: Optional[str] = None


class SpliceOut(SpliceIn):
    id: str
    passed: bool


class FloatingRunIn(BaseModel):
    pon_id: str
    segment_id: Optional[str] = None
    meters: Optional[float] = None
    drum_code: Optional[str] = None
    pull_method: Optional[str] = None
    lubricant_used: Optional[str] = None
    start_ts: Optional[str] = None


class FloatingRunCompleteIn(BaseModel):
    meters: float
    end_ts: Optional[str] = None
    photos_ok: bool = False
    passed: Optional[bool] = None


class FloatingRunOut(FloatingRunIn):
    id: str
    end_ts: Optional[str]
    photos_ok: bool
    passed: bool


class TestPlanIn(BaseModel):
    pon_id: str
    link_name: str
    from_point: Optional[str] = None
    to_point: Optional[str] = None
    wavelength_nm: int
    max_loss_db: float
    otdr_required: bool = False
    lspm_required: bool = False


class TestPlanOut(TestPlanIn):
    id: str


class OTDRResultIn(BaseModel):
    test_plan_id: str
    file_url: Optional[str] = None
    vendor: Optional[str] = None
    wavelength_nm: int
    total_loss_db: Optional[float] = None
    event_count: Optional[int] = None
    max_splice_loss_db: Optional[float] = None
    back_reflection_db: Optional[float] = None
    tested_at: Optional[str] = None


class OTDRResultOut(OTDRResultIn):
    id: str
    passed: bool


class LSPMResultIn(BaseModel):
    test_plan_id: str
    wavelength_nm: int
    measured_loss_db: float
    margin_db: Optional[float] = None
    tested_at: Optional[str] = None


class LSPMResultOut(LSPMResultIn):
    id: str
    passed: bool


class ConnectorInspectIn(BaseModel):
    closure_id: Optional[str] = None
    device_id: Optional[str] = None
    port: Optional[str] = None
    microscope_photo_url: Optional[str] = None
    grade: Optional[str] = None
    cleaned: bool = False
    retest_grade: Optional[str] = None
    tested_at: Optional[str] = None


class ConnectorInspectOut(ConnectorInspectIn):
    id: str
    passed: bool


class CableRegisterIn(BaseModel):
    pon_id: str
    cable_code: str
    type: Optional[str] = None
    length_m: Optional[int] = None
    drum_code: Optional[str] = None


class CableRegisterOut(CableRegisterIn):
    id: str
    installed_m: int


class CableInstalledUpdate(BaseModel):
    installed_m: int = Field(ge=0)


class TestPhotoIn(BaseModel):
    entity_type: str
    entity_id: str
    kind: str
    url: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    taken_ts: Optional[str] = None


class TestPhotoOut(TestPhotoIn):
    id: str
    exif_ok: bool
    within_geofence: bool

