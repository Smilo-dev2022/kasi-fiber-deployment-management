from datetime import datetime
from sqlalchemy import Integer, Enum as SAEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from db.base import Base


class InvoiceStatus(str, enum.Enum):
    Draft = "Draft"
    Submitted = "Submitted"
    Approved = "Approved"
    Paid = "Paid"


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    pon_id: Mapped[int] = mapped_column(ForeignKey("pons.id", ondelete="CASCADE"), index=True)
    smme_id: Mapped[int | None] = mapped_column(ForeignKey("smmes.id"), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[InvoiceStatus] = mapped_column(SAEnum(InvoiceStatus, name="invoice_status"), default=InvoiceStatus.Draft)
    submitted_at: Mapped[datetime | None]
    approved_by: Mapped[int | None]
    paid_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

