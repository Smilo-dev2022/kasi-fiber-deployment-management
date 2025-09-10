from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class MaintWindow(Base):
    __tablename__ = "maint_windows"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    scope = Column(String, nullable=False)  # device | pon | org | global
    target_id = Column(UUID(as_uuid=True), nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    approved_by = Column(String, nullable=True)

