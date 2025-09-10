from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class DeviceConfig(Base):
    __tablename__ = "device_configs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    source = Column(String, nullable=False)  # oxidized
    collected_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    sha256 = Column(String, nullable=False)


class GoldenTemplate(Base):
    __tablename__ = "golden_templates"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    role = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    model = Column(String, nullable=True)
    template = Column(Text, nullable=False)

