from datetime import datetime
from pydantic import BaseModel, Field


class InvoiceBase(BaseModel):
    id: int
    pon_id: int
    smme_id: int | None = None
    amount_cents: int
    status: str
    submitted_at: datetime | None = None
    approved_by: int | None = None
    paid_at: datetime | None = None

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    amount_cents: int = Field(..., ge=0)


class InvoiceUpdate(BaseModel):
    status: str | None = None


class InvoiceOut(InvoiceBase):
    pass

