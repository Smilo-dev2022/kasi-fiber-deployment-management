import uuid
from sqlalchemy import Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class StringingRun(Base):
    __tablename__ = "stringing_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"))
    meters: Mapped[float | None] = mapped_column(Numeric)
    brackets: Mapped[int | None] = mapped_column(Integer)
    dead_ends: Mapped[int | None] = mapped_column(Integer)
    tensioner: Mapped[int | None] = mapped_column(Integer)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
