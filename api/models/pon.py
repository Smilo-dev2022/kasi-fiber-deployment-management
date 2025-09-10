from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


class PON(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pon_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    street_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    homes_passed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poles_planned: Mapped[int] = mapped_column(Integer, default=0)
    poles_planted: Mapped[int] = mapped_column(Integer, default=0)
    cac_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    stringing_done: Mapped[bool] = mapped_column(Boolean, default=False)
    photos_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="Not Started")
    smme_id: Mapped[int | None] = mapped_column(ForeignKey("smme.id"), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    smme = relationship("SMME")

