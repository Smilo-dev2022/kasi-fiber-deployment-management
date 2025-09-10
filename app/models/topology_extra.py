from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Splitter(Base):
    __tablename__ = "splitters"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    closure_id = Column(UUID(as_uuid=True), ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True)
    code = Column(String, nullable=False)
    ratio = Column(Integer, nullable=False)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class SplitterPort(Base):
    __tablename__ = "splitter_ports"

    id = Column(UUID(as_uuid=True), primary_key=True)
    splitter_id = Column(UUID(as_uuid=True), ForeignKey("splitters.id", ondelete="CASCADE"), nullable=False)
    port_no = Column(Integer, nullable=False)
    tray_id = Column(UUID(as_uuid=True), ForeignKey("splice_trays.id", ondelete="SET NULL"), nullable=True)
    onu_device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)


class OLTPort(Base):
    __tablename__ = "olt_ports"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    port = Column(String, nullable=False)
    splitter_id = Column(UUID(as_uuid=True), ForeignKey("splitters.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class CableRegister(Base):
    __tablename__ = "cable_register"

    id = Column(UUID(as_uuid=True), primary_key=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    type = Column(String, nullable=False)
    polyline = Column(String, nullable=True)
    length_m = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)

