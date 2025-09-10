from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class OpticalIn(BaseModel):
    device_id: uuid.UUID
    pon_id: Optional[uuid.UUID] = None
    port: str
    direction: str
    dbm: float
    read_at: Optional[datetime] = None

