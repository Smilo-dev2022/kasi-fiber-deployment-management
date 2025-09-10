from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class TrenchSegment(Base):
    __tablename__ = "trench_segments"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"))
    start_gps = Column(String, nullable=True)
    end_gps = Column(String, nullable=True)
    length_m = Column(Numeric(), nullable=True)
    width_mm = Column(Integer, nullable=True)
    depth_mm = Column(Integer, nullable=True)
    surface_type = Column(String, nullable=True)
    status = Column(String, nullable=False, server_default="Planned")
    assigned_team = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    path_geojson = Column(Text, nullable=True)


class CivilsPhoto(Base):
    __tablename__ = "civils_photos"

    id = Column(UUID(as_uuid=True), primary_key=True)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("trench_segments.id", ondelete="CASCADE"))
    kind = Column(String, nullable=False)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    taken_ts = Column(DateTime(timezone=True), nullable=True)
    exif_ok = Column(Boolean, nullable=False, server_default="false")
    within_geofence = Column(Boolean, nullable=False, server_default="false")
    url = Column(String, nullable=False)


class DuctInstall(Base):
    __tablename__ = "duct_installs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("trench_segments.id", ondelete="CASCADE"))
    duct_type = Column(String, nullable=False)
    count = Column(Integer, nullable=False, server_default="1")
    rope_drawn = Column(Boolean, nullable=False, server_default="false")
    mandrel_passed = Column(Boolean, nullable=False, server_default="false")
    as_built_label = Column(String, nullable=True)


class Reinstatement(Base):
    __tablename__ = "reinstatements"

    id = Column(UUID(as_uuid=True), primary_key=True)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("trench_segments.id", ondelete="CASCADE"))
    surface_type = Column(String, nullable=False)
    area_m2 = Column(Numeric(), nullable=True)
    method = Column(String, nullable=True)
    passed = Column(Boolean, nullable=False, server_default="false")
    signed_off_by = Column(String, nullable=True)
    signed_off_at = Column(DateTime(timezone=True), nullable=True)

