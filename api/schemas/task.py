from datetime import datetime
from pydantic import BaseModel


class TaskBase(BaseModel):
    id: int
    pon_id: int
    step: str
    assigned_to: int | None = None
    smme_id: int | None = None
    status: str
    notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    step: str
    assigned_to: int | None = None
    smme_id: int | None = None
    notes: str | None = None


class TaskUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    assigned_to: int | None = None


class TaskOut(TaskBase):
    pass

