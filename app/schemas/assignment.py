from pydantic import BaseModel, Field
from typing import Optional
import uuid


class AssignmentCreate(BaseModel):
    org_id: uuid.UUID
    step_type: str = Field(regex="^(Civil|Technical|Maintenance|Sales)$")
    pon_id: Optional[uuid.UUID] = None
    ward: Optional[str] = None


class AssignmentOut(AssignmentCreate):
    id: uuid.UUID

    class Config:
        orm_mode = True

