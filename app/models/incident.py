from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    severity = Column(String, nullable=False)  # P1, P2, P3, P4
    category = Column(String, nullable=True)  # e.g., DeviceDown, LOS, OpticalLow, PowerLoss
    status = Column(String, nullable=False, default="Open")  # Open, Acknowledged, InProgress, Resolved, Closed
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)

    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)

    opened_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # SLA targets in minutes based on severity
    sla_response_min = Column(Integer, nullable=True)
    sla_restore_min = Column(Integer, nullable=True)
    breached_response = Column(Boolean, nullable=False, default=False, server_default="false")
    breached_restore = Column(Boolean, nullable=False, default=False, server_default="false")

    # Closure metadata
    root_cause = Column(String, nullable=True)
    fix_code = Column(String, nullable=True)
    close_notes = Column(String, nullable=True)
    close_photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id"), nullable=True)

