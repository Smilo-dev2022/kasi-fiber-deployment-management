from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.core.deps import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String, nullable=False)
    step_type = Column(String, nullable=True)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="SET NULL"), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=True)
    active = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

