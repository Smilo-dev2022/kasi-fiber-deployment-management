from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from db.base import Base


class CACCheck(Base):
    __tablename__ = "cac_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pons.id", ondelete="CASCADE"), index=True)
    pole_number: Mapped[str]
    pole_length_m: Mapped[float]
    depth_m: Mapped[float]
    tag_height_m: Mapped[float]
    hook_position: Mapped[str | None]
    alignment_ok: Mapped[bool]
    comments: Mapped[str | None]
    checked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    passed: Mapped[bool]
    checked_at: Mapped[datetime] = mapped_column(server_default=func.now())

    pon = relationship("PON", back_populates="cac_checks")

