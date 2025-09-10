import uuid
from sqlalchemy import String, Integer, Boolean, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class PON(Base):
    __tablename__ = "pons"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pon_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    ward: Mapped[str | None] = mapped_column(String)
    street_area: Mapped[str | None] = mapped_column(String)
    homes_passed: Mapped[int] = mapped_column(Integer, default=0)
    poles_planned: Mapped[int] = mapped_column(Integer, default=0)
    poles_planted: Mapped[int] = mapped_column(Integer, default=0)
    cac_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    stringing_done: Mapped[bool] = mapped_column(Boolean, default=False)
    photos_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, server_default=text("'Not Started'"))
    smme_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("smmes.id"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
