from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class SpliceClosure(Base):
    __tablename__ = "splice_closures"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, unique=True, nullable=False)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    enclosure_type = Column(String, nullable=True)
    tray_count = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="Planned", server_default="Planned")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class SpliceTray(Base):
    __tablename__ = "splice_trays"

    id = Column(UUID(as_uuid=True), primary_key=True)
    closure_id = Column(UUID(as_uuid=True), ForeignKey("splice_closures.id", ondelete="CASCADE"), nullable=False)
    tray_no = Column(Integer, nullable=False)
    fiber_start = Column(Integer, nullable=True)
    fiber_end = Column(Integer, nullable=True)
    splices_planned = Column(Integer, nullable=True)
    splices_done = Column(Integer, nullable=False, default=0, server_default="0")


class Splice(Base):
    __tablename__ = "splices"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tray_id = Column(UUID(as_uuid=True), ForeignKey("splice_trays.id", ondelete="CASCADE"), nullable=False)
    core = Column(Integer, nullable=False)
    from_cable = Column(String, nullable=True)
    to_cable = Column(String, nullable=True)
    loss_db = Column(Numeric(5, 3), nullable=True)
    method = Column(String, nullable=True)
    tech_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    time = Column(DateTime(timezone=True), nullable=True)
    passed = Column(Boolean, nullable=False, default=False, server_default="false")


class FloatingRun(Base):
    __tablename__ = "floating_runs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("trench_segments.id", ondelete="SET NULL"), nullable=True)
    meters = Column(Numeric(10, 2), nullable=True)
    drum_code = Column(String, nullable=True)
    pull_method = Column(String, nullable=True)
    lubricant_used = Column(String, nullable=True)
    start_ts = Column(DateTime(timezone=True), nullable=True)
    end_ts = Column(DateTime(timezone=True), nullable=True)
    photos_ok = Column(Boolean, nullable=False, default=False, server_default="false")
    passed = Column(Boolean, nullable=False, default=False, server_default="false")


class TestPlan(Base):
    __tablename__ = "test_plans"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    link_name = Column(String, nullable=False)
    from_point = Column(String, nullable=True)
    to_point = Column(String, nullable=True)
    wavelength_nm = Column(Integer, nullable=False)
    max_loss_db = Column(Numeric(5, 2), nullable=False)
    otdr_required = Column(Boolean, nullable=False, default=False, server_default="false")
    lspm_required = Column(Boolean, nullable=False, default=False, server_default="false")


class OTDRResult(Base):
    __tablename__ = "otdr_results"

    id = Column(UUID(as_uuid=True), primary_key=True)
    test_plan_id = Column(UUID(as_uuid=True), ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False)
    file_url = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    wavelength_nm = Column(Integer, nullable=False)
    total_loss_db = Column(Numeric(5, 2), nullable=True)
    event_count = Column(Integer, nullable=True)
    max_splice_loss_db = Column(Numeric(5, 2), nullable=True)
    back_reflection_db = Column(Numeric(5, 2), nullable=True)
    tested_at = Column(DateTime(timezone=True), nullable=True)
    passed = Column(Boolean, nullable=False, default=False, server_default="false")


class LSPMResult(Base):
    __tablename__ = "lspm_results"

    id = Column(UUID(as_uuid=True), primary_key=True)
    test_plan_id = Column(UUID(as_uuid=True), ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False)
    wavelength_nm = Column(Integer, nullable=False)
    measured_loss_db = Column(Numeric(5, 2), nullable=False)
    margin_db = Column(Numeric(5, 2), nullable=True)
    tested_at = Column(DateTime(timezone=True), nullable=True)
    passed = Column(Boolean, nullable=False, default=False, server_default="false")


class ConnectorInspect(Base):
    __tablename__ = "connector_inspects"

    id = Column(UUID(as_uuid=True), primary_key=True)
    closure_id = Column(UUID(as_uuid=True), ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    port = Column(String, nullable=True)
    microscope_photo_url = Column(String, nullable=True)
    grade = Column(String, nullable=True)
    cleaned = Column(Boolean, nullable=False, default=False, server_default="false")
    retest_grade = Column(String, nullable=True)
    tested_at = Column(DateTime(timezone=True), nullable=True)
    passed = Column(Boolean, nullable=False, default=False, server_default="false")


class CableRegister(Base):
    __tablename__ = "cable_register"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    cable_code = Column(String, nullable=False)
    type = Column(String, nullable=True)
    length_m = Column(Integer, nullable=True)
    drum_code = Column(String, nullable=True)
    installed_m = Column(Integer, nullable=False, default=0, server_default="0")


class TestPhoto(Base):
    __tablename__ = "test_photos"

    id = Column(UUID(as_uuid=True), primary_key=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    kind = Column(String, nullable=False)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    taken_ts = Column(DateTime(timezone=True), nullable=True)
    exif_ok = Column(Boolean, nullable=False, default=False, server_default="false")
    within_geofence = Column(Boolean, nullable=False, default=False, server_default="false")
    url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

