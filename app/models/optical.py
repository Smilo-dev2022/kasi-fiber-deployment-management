from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class OpticalReading(Base):
    __tablename__ = "optical_readings"

    id = Column(UUID(as_uuid=True), primary_key=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    onu_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)  # ONT/ONU device id
    port_name = Column(String, nullable=True)  # e.g., gpon0/1, PON1, or ONT UNI1
    direction = Column(String, nullable=True)  # OLT_RX, OLT_TX, ONU_RX, ONU_TX
    dBm = Column(Numeric(5, 2), nullable=True)
    taken_at = Column(DateTime(timezone=True), nullable=False)

