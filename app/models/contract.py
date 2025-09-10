from sqlalchemy import Column, String, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import ForeignKey, DateTime
from app.core.deps import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String, nullable=False)
    wards = Column(ARRAY(UUID(as_uuid=True)))
    sla_minutes_p1 = Column(Integer, nullable=False)
    sla_minutes_p2 = Column(Integer, nullable=False)
    sla_minutes_p3 = Column(Integer, nullable=False)
    sla_minutes_p4 = Column(Integer, nullable=False)
    rate_card = Column(JSON, nullable=True)
    active = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

