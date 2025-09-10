from sqlalchemy import Column, String, DateTime, Boolean, Integer, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.deps import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    hostname = Column(String, nullable=False, unique=True)
    device_type = Column(String, nullable=False)  # OLT, SWITCH, ROUTER, ODF
    vendor = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial = Column(String, nullable=True)
    ward = Column(String, nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    gps_lat = Column(Numeric(9, 6), nullable=True)
    gps_lng = Column(Numeric(9, 6), nullable=True)
    status = Column(String, nullable=False, server_default="Unknown")
    last_up_ts = Column(DateTime(timezone=True), nullable=True)
    last_down_ts = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Port(Base):
    __tablename__ = "ports"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    if_index = Column(Integer, nullable=True)
    port_type = Column(String, nullable=True)  # Ethernet, PON, Uplink
    status = Column(String, nullable=True)
    onu_count = Column(Integer, nullable=False, server_default="0")
    last_optical_dbm = Column(Numeric(5, 2), nullable=True)
    last_changed_at = Column(DateTime(timezone=True), nullable=True)


class ONU(Base):
    __tablename__ = "onus"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)  # OLT
    port_id = Column(UUID(as_uuid=True), ForeignKey("ports.id", ondelete="SET NULL"), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    serial = Column(String, nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, nullable=True)
    last_optical_dbm = Column(Numeric(5, 2), nullable=True)
    last_seen_ts = Column(DateTime(timezone=True), nullable=True)
    last_up_ts = Column(DateTime(timezone=True), nullable=True)
    last_down_ts = Column(DateTime(timezone=True), nullable=True)
    flap_count = Column(Integer, nullable=False, server_default="0")


class OpticalReading(Base):
    __tablename__ = "optical_readings"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    port_id = Column(UUID(as_uuid=True), ForeignKey("ports.id", ondelete="CASCADE"), nullable=True)
    onu_id = Column(UUID(as_uuid=True), ForeignKey("onus.id", ondelete="CASCADE"), nullable=True)
    kind = Column(String, nullable=False)  # OLT_RX, ONU_RX, TX
    value_dbm = Column(Numeric(5, 2), nullable=False)
    taken_ts = Column(DateTime(timezone=True), nullable=False)


class OpticalBaseline(Base):
    __tablename__ = "optical_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    port_id = Column(UUID(as_uuid=True), ForeignKey("ports.id", ondelete="CASCADE"), nullable=True)
    onu_id = Column(UUID(as_uuid=True), ForeignKey("onus.id", ondelete="CASCADE"), nullable=True)
    kind = Column(String, nullable=False)
    baseline_dbm = Column(Numeric(5, 2), nullable=False)
    set_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    category = Column(String, nullable=False)  # DeviceDown, OpticalLow, PortDown, Clear
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="Open")
    dedup_key = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    port_id = Column(UUID(as_uuid=True), ForeignKey("ports.id", ondelete="SET NULL"), nullable=True)
    onu_id = Column(UUID(as_uuid=True), ForeignKey("onus.id", ondelete="SET NULL"), nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    ward = Column(String, nullable=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    ttd_seconds = Column(Integer, nullable=True)
    ttr_seconds = Column(Integer, nullable=True)
    sla_due_at = Column(DateTime(timezone=True), nullable=True)
    breached = Column(Boolean, nullable=False, server_default="false")
    requires_photo = Column(Boolean, nullable=False, server_default="false")
    requires_optical = Column(Boolean, nullable=False, server_default="false")
    root_cause = Column(String, nullable=True)
    fix_code = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    paged = Column(Boolean, nullable=False, server_default="false")


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    scope_type = Column(String, nullable=False)  # GLOBAL, WARD, PON, DEVICE
    ward = Column(String, nullable=True)
    pon_id = Column(UUID(as_uuid=True), ForeignKey("pons.id"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, server_default="Approved")
    pre_check_done = Column(Boolean, nullable=False, server_default="false")
    post_check_done = Column(Boolean, nullable=False, server_default="false")
    created_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String, nullable=True)
    source = Column(String, nullable=False)
    received_ip = Column(String, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    hmac_valid = Column(Boolean, nullable=False, server_default="false")
    payload = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    request_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

