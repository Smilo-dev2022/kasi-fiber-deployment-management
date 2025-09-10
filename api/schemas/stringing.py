from datetime import datetime
from pydantic import BaseModel, Field


class StringingRunBase(BaseModel):
    id: int
    pon_id: int
    meters: float
    brackets: int
    dead_ends: int
    tensioner: int
    completed_by: int | None = None
    completed_at: datetime

    class Config:
        from_attributes = True


class StringingRunCreate(BaseModel):
    meters: float = Field(..., ge=0)
    brackets: int = Field(0, ge=0)
    dead_ends: int = Field(0, ge=0)
    tensioner: int = Field(0, ge=0)


class StringingRunOut(StringingRunBase):
    pass

