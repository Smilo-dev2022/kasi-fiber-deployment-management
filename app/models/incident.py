from sqlalchemy import Column, String, DateTime, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    severity = Column(String, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, server_default=text("'Open'"))
    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    ack_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    root_cause = Column(String, nullable=True)
    fix_code = Column(String, nullable=True)
    nms_ref = Column(String, nullable=True)

