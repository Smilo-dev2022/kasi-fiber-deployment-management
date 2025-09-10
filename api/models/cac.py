from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class CACCheck(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pon.id"), index=True)
    pole_number: Mapped[str]
    pole_length_m: Mapped[float] = mapped_column(Float)
    depth_m: Mapped[float] = mapped_column(Float)
    tag_height_m: Mapped[float] = mapped_column(Float)
    hook_position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alignment_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    comments: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    checked_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

