from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from db.base import Base


class StringingRun(Base):
    __tablename__ = "stringing_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pons.id", ondelete="CASCADE"), index=True)
    meters: Mapped[int]
    brackets: Mapped[int]
    dead_ends: Mapped[int]
    tensioner: Mapped[int]
    completed_by: Mapped[int | None]
    completed_at: Mapped[datetime | None]

    pon = relationship("PON", back_populates="stringing_runs")

