from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)

