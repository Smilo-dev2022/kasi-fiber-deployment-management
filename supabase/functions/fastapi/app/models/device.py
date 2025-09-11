from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial = Column(String, nullable=True)
    mgmt_ip = Column(String, nullable=True)
    site = Column(String, nullable=True)
    status = Column(String, nullable=True, default="Active")
    created_at = Column(DateTime(timezone=True), nullable=True)


class DeviceConfig(Base):
    __tablename__ = "device_configs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    running_config = Column(Text, nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    hash_sha256 = Column(String, nullable=False)


class GoldenTemplate(Base):
    __tablename__ = "golden_templates"

    id = Column(UUID(as_uuid=True), primary_key=True)
    device_role = Column(String, nullable=False)
    template_text = Column(Text, nullable=False)
    policy_regex_deny = Column(Text, nullable=True)
