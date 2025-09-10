from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class SMME(Base):
    __tablename__ = "smmes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
