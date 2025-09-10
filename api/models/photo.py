from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pons.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    url: Mapped[str] = mapped_column(String(1024))
    kind: Mapped[str] = mapped_column(String(50))
    taken_at: Mapped[datetime | None] = mapped_column(nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    pon = relationship("PON", back_populates="photos")

