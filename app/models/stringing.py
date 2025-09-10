from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class StringingRun(Base):
    __tablename__ = "stringing_runs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), nullable=True)
    meters = Column(Numeric(8, 2), nullable=False)
    brackets = Column(Integer, nullable=True)
    dead_ends = Column(Integer, nullable=True)
    tensioners = Column(Integer, nullable=True)
    start_ts = Column(DateTime(timezone=True), nullable=True)
    end_ts = Column(DateTime(timezone=True), nullable=True)
    photos_ok = Column(Boolean, nullable=False, default=False, server_default="false")
    qc_passed = Column(Boolean, nullable=False, default=False, server_default="false")
    created_by = Column(UUID(as_uuid=True), nullable=True)

