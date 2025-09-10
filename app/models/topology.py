from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class TopoNode(Base):
    __tablename__ = "topo_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    code = Column(String, nullable=False)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)


class TopoEdge(Base):
    __tablename__ = "topo_edges"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    a_id = Column(UUID(as_uuid=True), ForeignKey("topo_nodes.id", ondelete="CASCADE"), nullable=False)
    b_id = Column(UUID(as_uuid=True), ForeignKey("topo_nodes.id", ondelete="CASCADE"), nullable=False)
    cable_code = Column(String, nullable=True)
    length_m = Column(Numeric(), nullable=True)

