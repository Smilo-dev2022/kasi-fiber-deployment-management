from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import uuid


class ContractCreate(BaseModel):
    org_id: uuid.UUID
    scope: str = Field(regex="^(Civil|Technical|Maintenance|Sales)$")
    wards: Optional[List[str]] = None
    sla_p1_minutes: Optional[int] = None
    sla_p2_minutes: Optional[int] = None
    sla_p3_minutes: Optional[int] = None
    sla_p4_minutes: Optional[int] = None
    rate_card_id: Optional[uuid.UUID] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class ContractOut(ContractCreate):
    id: uuid.UUID

    class Config:
        orm_mode = True

