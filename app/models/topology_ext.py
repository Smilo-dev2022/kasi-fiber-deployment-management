from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Splitter(Base):
    __tablename__ = "splitters"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"))
    closure_id = Column(UUID(as_uuid=True), ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True)
    code = Column(String, nullable=False)
    ratio = Column(String, nullable=True)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    status = Column(String, nullable=False)


class PortMap(Base):
    __tablename__ = "port_map"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"))
    olt_device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    olt_port = Column(String, nullable=True)
    splitter_id = Column(UUID(as_uuid=True), ForeignKey("splitters.id", ondelete="SET NULL"), nullable=True)
    branch_no = Column(Integer, nullable=True)
    onu_device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    drop_code = Column(String, nullable=True)


class CableRegister(Base):
    __tablename__ = "cable_register"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"))
    cable_code = Column(String, nullable=False)
    polyline = Column(String, nullable=True)
    length_m = Column(Numeric(), nullable=True)

