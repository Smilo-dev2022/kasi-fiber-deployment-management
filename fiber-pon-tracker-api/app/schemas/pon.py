from pydantic import BaseModel
from typing import Optional
import uuid


class PONBase(BaseModel):
    pon_number: str
    ward: Optional[str] = None
    street_area: Optional[str] = None
    homes_passed: int = 0
    poles_planned: int = 0


class PONCreate(PONBase):
    pass


class PONUpdate(BaseModel):
    ward: Optional[str] = None
    street_area: Optional[str] = None
    homes_passed: Optional[int] = None
    poles_planned: Optional[int] = None
    poles_planted: Optional[int] = None
    cac_passed: Optional[bool] = None
    stringing_done: Optional[bool] = None
    photos_uploaded: Optional[bool] = None
    status: Optional[str] = None
    smme_id: Optional[uuid.UUID] = None


class PONOut(PONBase):
    id: uuid.UUID
    poles_planted: int
    cac_passed: bool
    stringing_done: bool
    photos_uploaded: bool
    status: str
    smme_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
