from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class StringingRun(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pon.id"), index=True)
    meters: Mapped[float] = mapped_column(Float, default=0)
    brackets: Mapped[int] = mapped_column(Integer, default=0)
    dead_ends: Mapped[int] = mapped_column(Integer, default=0)
    tensioner: Mapped[int] = mapped_column(Integer, default=0)
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

