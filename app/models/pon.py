from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class PON(Base):
    __tablename__ = "pons"

    id = Column(UUID(as_uuid=True), primary_key=True)
    status = Column(String, nullable=True)
    center_lat = Column(Numeric(9, 6), nullable=True)
    center_lng = Column(Numeric(9, 6), nullable=True)
    geofence_radius_m = Column(Integer, nullable=False, default=200, server_default="200")
    sla_breaches = Column(Integer, nullable=False, default=0, server_default="0")
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="SET NULL"), nullable=True)

