from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    taken_at = Column(DateTime(timezone=True), nullable=True)
    taken_ts = Column(DateTime(timezone=True), nullable=True)
    exif_ok = Column(Boolean, nullable=False, default=False, server_default="false")
    within_geofence = Column(Boolean, nullable=False, default=False, server_default="false")
    asset_code = Column(String, nullable=True)

