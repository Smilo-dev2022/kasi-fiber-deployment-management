from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class StockItem(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(10))  # ea or drum
    on_hand: Mapped[float] = mapped_column(Float, default=0)
    __table_args__ = (
        CheckConstraint("on_hand >= 0", name="ck_stockitem_on_hand_nonnegative"),
    )


class StockIssue(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stockitem.id"), index=True)
    pon_id: Mapped[int | None] = mapped_column(ForeignKey("pon.id"), nullable=True)
    issued_to: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    quantity: Mapped[float] = mapped_column(Float)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

