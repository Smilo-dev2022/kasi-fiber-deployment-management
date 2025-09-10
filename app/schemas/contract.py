from pydantic import BaseModel
from typing import Optional


class ContractIn(BaseModel):
    org_id: str
    scope: str
    sla_p1_minutes: Optional[int] = None
    sla_p2_minutes: Optional[int] = None
    sla_p3_minutes: Optional[int] = None
    sla_p4_minutes: Optional[int] = None
    valid_from: str
    valid_to: Optional[str] = None


class AssignmentIn(BaseModel):
    org_id: str
    step: str
    pon_id: Optional[str] = None
    ward_code: Optional[str] = None

