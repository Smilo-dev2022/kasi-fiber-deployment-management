import uuid

from sqlalchemy import String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.deps import Base


class OpticalReading(Base):
    __tablename__ = "optical_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    pon_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    port: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    dbm: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    read_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

