from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    smmme_id = Column(UUID(as_uuid=True), ForeignKey("smmes.id"), nullable=True)  # note: name as referenced in SQL
    step = Column(String, nullable=True)
    status = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    sla_minutes = Column(Integer, nullable=True)
    sla_due_at = Column(DateTime(timezone=True), nullable=True)
    breached = Column(Boolean, nullable=False, default=False, server_default="false")

