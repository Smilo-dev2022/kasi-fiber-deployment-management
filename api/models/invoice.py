from datetime import datetime
from sqlalchemy import Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class Invoice(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pon.id"), index=True)
    smme_id: Mapped[int | None] = mapped_column(ForeignKey("smme.id"), nullable=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(20), default="Draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

