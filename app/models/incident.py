import uuid

from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.deps import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    pon_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))
    severity: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Open")
    opened_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ack_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    root_cause: Mapped[str | None] = mapped_column(String, nullable=True)
    fix_code: Mapped[str | None] = mapped_column(String, nullable=True)
    nms_ref: Mapped[str | None] = mapped_column(String, nullable=True)

