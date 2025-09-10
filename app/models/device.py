from sqlalchemy import Column, String, DateTime, Boolean, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True)
    # Types: OLT, ONU, ONT, SWITCH, ROUTER, SPLITTER, UPS, GENERATOR, BATTERY, SENSOR
    kind = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial = Column(String, nullable=True, index=True)
    mgmt_ip = Column(String, nullable=True, index=True)
    site = Column(String, nullable=True)
    tenant = Column(String, nullable=True)
    role = Column(String, nullable=True)  # e.g., CORE, ACCESS, AGG, CPE
    status = Column(String, nullable=True)  # e.g., Up, Down, Maintenance
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    uptime_seconds = Column(Integer, nullable=True)

    # Optional mapping to PON for access network elements
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)

