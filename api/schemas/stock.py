from datetime import datetime
from pydantic import BaseModel, Field


class StockItemBase(BaseModel):
    id: int
    sku: str
    name: str
    unit: str
    on_hand: float

    class Config:
        from_attributes = True


class StockItemCreate(BaseModel):
    sku: str
    name: str
    unit: str
    on_hand: float = Field(0, ge=0)


class StockItemOut(StockItemBase):
    pass


class StockIssueBase(BaseModel):
    id: int
    item_id: int
    pon_id: int | None = None
    issued_to: int | None = None
    quantity: float
    issued_at: datetime

    class Config:
        from_attributes = True


class StockIssueCreate(BaseModel):
    item_id: int
    pon_id: int | None = None
    issued_to: int | None = None
    quantity: float = Field(..., gt=0)


class StockIssueOut(StockIssueBase):
    pass

