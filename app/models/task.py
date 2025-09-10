from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    step = Column(String, nullable=False)
    status = Column(String, nullable=False, default="New")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    sla_minutes = Column(Integer, nullable=True)
    sla_due_at = Column(DateTime(timezone=True), nullable=True)
    breached = Column(Boolean, nullable=False, default=False)
