from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String, nullable=False)
    wards = Column(String, nullable=True)
    sla_p1_minutes = Column(Integer, nullable=True)
    sla_p2_minutes = Column(Integer, nullable=True)
    sla_p3_minutes = Column(Integer, nullable=True)
    sla_p4_minutes = Column(Integer, nullable=True)
    rate_card_id = Column(UUID(as_uuid=True), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

