from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    taken_at = Column(DateTime(timezone=True), nullable=True)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    taken_ts = Column(DateTime(timezone=True), nullable=True)
    exif_ok = Column(Boolean, nullable=False, default=False)
    within_geofence = Column(Boolean, nullable=False, default=False)
    asset_code = Column(String, nullable=True)
