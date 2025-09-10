import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

from app.core.deps import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    pon_id = Column(
        UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"), nullable=True
    )
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial = Column(String, nullable=True)
    mgmt_ip = Column(String, nullable=True)
    site = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Active", server_default="Active")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

