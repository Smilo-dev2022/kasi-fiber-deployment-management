from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CACCheckBase(BaseModel):
    id: int
    pon_id: int
    pole_number: str
    pole_length_m: float
    depth_m: float
    tag_height_m: float
    hook_position: str | None = None
    alignment_ok: bool
    comments: str | None = None
    checked_by: int | None = None
    passed: bool
    checked_at: datetime

    class Config:
        from_attributes = True


class CACCheckCreate(BaseModel):
    pole_number: str
    pole_length_m: float = Field(..., ge=7.4, le=7.8)
    depth_m: float = Field(..., ge=1.1, le=1.2)
    tag_height_m: float = Field(..., ge=2.2, le=2.3)
    hook_position: str | None = None
    alignment_ok: bool = True
    comments: str | None = None
    passed: bool


class CACCheckOut(CACCheckBase):
    pass

