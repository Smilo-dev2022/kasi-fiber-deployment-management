from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class SMME(Base):
    __tablename__ = "smmes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

