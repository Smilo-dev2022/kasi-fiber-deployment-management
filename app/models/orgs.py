from sqlalchemy import Column, String, Date, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.deps import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    scope_type = Column(String, nullable=False)
    wards = Column(ARRAY(String), nullable=True)
    sla_p1_min = Column(Integer, nullable=True)
    sla_p2_min = Column(Integer, nullable=True)
    sla_p3_min = Column(Integer, nullable=True)
    sla_p4_min = Column(Integer, nullable=True)
    rate_card_ref = Column(String, nullable=True)
    active = Column(Boolean, nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=True)
    ward = Column(String, nullable=True)
    step_type = Column(String, nullable=False)


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    org_id = Column(UUID(as_uuid=True))
    name = Column(String, nullable=False)
    token_hash = Column(String, nullable=False)
    scope = Column(String, nullable=False)

