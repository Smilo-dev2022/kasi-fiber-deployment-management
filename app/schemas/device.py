from typing import Optional
import uuid

from pydantic import BaseModel


class DeviceCreate(BaseModel):
    name: str
    role: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    mgmt_ip: Optional[str] = None
    site: Optional[str] = None
    pon_id: Optional[uuid.UUID] = None


class DeviceOut(DeviceCreate):
    id: uuid.UUID
    status: str

    class Config:
        orm_mode = True

