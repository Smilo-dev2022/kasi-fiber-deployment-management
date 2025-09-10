from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class CACCheck(Base):
    __tablename__ = "cac_checks"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=False)
    pole_number = Column(String, nullable=True)
    pole_length_m = Column(Numeric(4, 2), nullable=False)
    depth_m = Column(Numeric(3, 2), nullable=False)
    tag_height_m = Column(Numeric(3, 2), nullable=False)
    hook_position = Column(String, nullable=True)
    alignment_ok = Column(Boolean, nullable=False, default=True, server_default="true")
    comments = Column(String, nullable=True)
    passed = Column(Boolean, nullable=False, default=True, server_default="true")

