import uuid
from sqlalchemy import String, ForeignKey, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class CACCheck(Base):
    __tablename__ = "cac_checks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"))
    pole_number: Mapped[str | None] = mapped_column(String)
    pole_length_m: Mapped[float | None] = mapped_column(Numeric)
    depth_m: Mapped[float | None] = mapped_column(Numeric)
    tag_height_m: Mapped[float | None] = mapped_column(Numeric)
    hook_position: Mapped[str | None] = mapped_column(String)
    alignment_ok: Mapped[bool | None] = mapped_column(Boolean)
    comments: Mapped[str | None] = mapped_column(String)
    checked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    passed: Mapped[bool | None] = mapped_column(Boolean)
    checked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
