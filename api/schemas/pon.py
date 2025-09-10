from datetime import datetime
from pydantic import BaseModel


class PONBase(BaseModel):
    id: int
    pon_number: str
    ward: str | None = None
    street_area: str | None = None
    homes_passed: int | None = None
    poles_planned: int
    poles_planted: int
    cac_passed: bool
    stringing_done: bool
    photos_uploaded: bool
    status: str
    smme_id: int | None = None
    created_by: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class PONCreate(BaseModel):
    pon_number: str
    ward: str | None = None
    street_area: str | None = None
    homes_passed: int | None = None
    poles_planned: int = 0
    smme_id: int | None = None


class PONUpdate(BaseModel):
    ward: str | None = None
    street_area: str | None = None
    homes_passed: int | None = None
    poles_planned: int | None = None
    poles_planted: int | None = None


class PONOut(PONBase):
    pass

