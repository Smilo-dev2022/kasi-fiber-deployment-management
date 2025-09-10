from sqlalchemy import Column, String, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.core.deps import Base


class OLTPort(Base):
    __tablename__ = "olt_ports"

    id = Column(UUID(as_uuid=True), primary_key=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    max_onu = Column(Integer, nullable=True)


class Splitter(Base):
    __tablename__ = "splitters"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    closure_id = Column(UUID(as_uuid=True), ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True)
    code = Column(String, nullable=False)
    ratio = Column(String, nullable=False)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)


class PortMap(Base):
    __tablename__ = "port_maps"

    id = Column(UUID(as_uuid=True), primary_key=True)
    olt_port_id = Column(UUID(as_uuid=True), ForeignKey("olt_ports.id", ondelete="CASCADE"), nullable=False)
    splitter_id = Column(UUID(as_uuid=True), ForeignKey("splitters.id", ondelete="CASCADE"), nullable=False)
    splitter_port = Column(Integer, nullable=True)
    onu_device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    drop_length_m = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

