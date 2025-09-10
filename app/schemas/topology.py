from pydantic import BaseModel
from typing import Optional, List
import uuid


class TopoNodeOut(BaseModel):
    id: uuid.UUID
    pon_id: uuid.UUID
    type: str
    code: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

    class Config:
        orm_mode = True


class TopoEdgeOut(BaseModel):
    id: uuid.UUID
    pon_id: uuid.UUID
    a_id: uuid.UUID
    b_id: uuid.UUID
    cable_code: Optional[str] = None
    length_m: Optional[float] = None

    class Config:
        orm_mode = True


class TopologyOut(BaseModel):
    nodes: List[TopoNodeOut]
    edges: List[TopoEdgeOut]


class TopologyEdgesImportResult(BaseModel):
    created_nodes: int
    created_edges: int
    updated_edges: int
    skipped: int

