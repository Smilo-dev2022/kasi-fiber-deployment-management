from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class Photo(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pon.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("task.id"), nullable=True)
    url: Mapped[str] = mapped_column(String(1024))
    kind: Mapped[str] = mapped_column(String(50))  # Dig, Plant, CAC, Stringing
    taken_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

