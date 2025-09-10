from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class OpticalReading(Base):
    __tablename__ = "optical_readings"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    port = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    dbm = Column(Numeric(6, 2), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

