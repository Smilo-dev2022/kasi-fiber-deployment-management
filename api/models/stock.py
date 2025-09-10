from datetime import datetime
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from db.base import Base


class StockUnit(str, enum.Enum):
    ea = "ea"
    drum = "drum"


class StockItem(Base):
    __tablename__ = "stock_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[StockUnit] = mapped_column(SAEnum(StockUnit, name="stock_unit"))
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=0)


class StockIssue(Base):
    __tablename__ = "stock_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"))
    pon_id: Mapped[int | None] = mapped_column(ForeignKey("pons.id"), nullable=True)
    issued_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    quantity: Mapped[int]
    issued_at: Mapped[datetime] = mapped_column(server_default=func.now())

