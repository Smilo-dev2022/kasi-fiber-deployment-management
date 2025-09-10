from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class Task(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pon.id"), index=True)
    step: Mapped[str] = mapped_column(String(50))
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    smme_id: Mapped[int | None] = mapped_column(ForeignKey("smme.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

