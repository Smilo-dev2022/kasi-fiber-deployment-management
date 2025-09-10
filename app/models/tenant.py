from sqlalchemy import Column, String, Boolean, DateTime, BigInteger, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    plan = Column(String, nullable=False, server_default="Starter")
    status = Column(String, nullable=False, server_default="Active")
    flags = Column(JSON, nullable=False, server_default='{}')
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


class TenantDomain(Base):
    __tablename__ = "tenant_domains"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String, nullable=False)
    is_primary = Column(Boolean, nullable=False, server_default="false")

    __table_args__ = (
        UniqueConstraint("domain", name="uq_tenant_domain_domain"),
    )


class TenantTheme(Base):
    __tablename__ = "tenant_themes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    theme = Column(JSON, nullable=False, server_default='{}')
    logo_url = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    pdf_footer = Column(String, nullable=True)


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Boolean, nullable=False, server_default="false")

    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_feature_flag_key"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    actor_email = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    ip = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True))


class MeteringCounter(Base):
    __tablename__ = "metering_counters"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    metric = Column(String, nullable=False)
    period = Column(String, nullable=False)  # e.g., 2025-09
    value = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "metric", "period", name="uq_metering_counter"),
    )


class TenantFileKey(Base):
    __tablename__ = "tenant_file_keys"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    kms_key_arn = Column(String, nullable=True)
    storage_prefix = Column(String, nullable=False)  # e.g., s3://bucket/tenants/{tenant_id}/

