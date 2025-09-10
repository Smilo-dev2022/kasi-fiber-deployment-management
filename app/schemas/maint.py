from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class MaintWindowCreate(BaseModel):
    scope: str
    target_id: Optional[uuid.UUID] = None
    start_at: datetime
    end_at: datetime
    approved_by: Optional[str] = None


class MaintWindowOut(MaintWindowCreate):
    id: uuid.UUID

    class Config:
        orm_mode = True

