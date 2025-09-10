from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class IncidentCreate(BaseModel):
    title: str
    severity: str
    category: str
    description: Optional[str] = None
    pon_id: Optional[uuid.UUID] = None
    device_id: Optional[uuid.UUID] = None
    nms_ref: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    ack_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    fix_code: Optional[str] = None


class IncidentOut(IncidentCreate, IncidentUpdate):
    id: uuid.UUID

    class Config:
        orm_mode = True

