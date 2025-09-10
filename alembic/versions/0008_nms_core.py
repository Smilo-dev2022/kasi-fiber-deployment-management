from alembic import op
import sqlalchemy as sa


revision = "0008_nms_core"
down_revision = "0007_civils_core"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "devices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hostname", sa.String(), nullable=False, unique=True),
        sa.Column("device_type", sa.String(), nullable=False),
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("serial", sa.String(), nullable=True),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Unknown'"), nullable=False),
        sa.Column("last_up_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_down_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_devices_tenant", "devices", ["tenant_id"]) 
    op.create_index("idx_devices_pon", "devices", ["pon_id"]) 
    op.create_index("idx_devices_ward", "devices", ["ward"]) 

    op.create_table(
        "ports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("if_index", sa.Integer(), nullable=True),
        sa.Column("port_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("onu_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_optical_dbm", sa.Numeric(5, 2), nullable=True),
        sa.Column("last_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_ports_device", "ports", ["device_id"]) 

    op.create_table(
        "onus",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("port_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("ports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("serial", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("last_optical_dbm", sa.Numeric(5, 2), nullable=True),
        sa.Column("last_seen_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_up_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_down_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("flap_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("idx_onus_device", "onus", ["device_id"]) 
    op.create_index("idx_onus_port", "onus", ["port_id"]) 
    op.create_index("idx_onus_serial", "onus", ["serial"]) 

    op.create_table(
        "optical_readings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=True),
        sa.Column("port_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("ports.id", ondelete="CASCADE"), nullable=True),
        sa.Column("onu_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("onus.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("value_dbm", sa.Numeric(5, 2), nullable=False),
        sa.Column("taken_ts", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_optical_readings_onu", "optical_readings", ["onu_id"]) 
    op.create_index("idx_optical_readings_port", "optical_readings", ["port_id"]) 
    op.create_index("idx_optical_readings_device", "optical_readings", ["device_id"]) 
    op.create_index("idx_optical_readings_time", "optical_readings", ["taken_ts"]) 

    op.create_table(
        "optical_baselines",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=True),
        sa.Column("port_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("ports.id", ondelete="CASCADE"), nullable=True),
        sa.Column("onu_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("onus.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("baseline_dbm", sa.Numeric(5, 2), nullable=False),
        sa.Column("set_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
    )
    op.create_index("idx_optical_baselines_onu", "optical_baselines", ["onu_id"]) 
    op.create_index("idx_optical_baselines_port", "optical_baselines", ["port_id"]) 

    op.create_table(
        "incidents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Open'"), nullable=False),
        sa.Column("dedup_key", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("port_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("ports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("onu_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("onus.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ttd_seconds", sa.Integer(), nullable=True),
        sa.Column("ttr_seconds", sa.Integer(), nullable=True),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("breached", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("requires_photo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("requires_optical", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("root_cause", sa.String(), nullable=True),
        sa.Column("fix_code", sa.String(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("paged", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_incidents_status", "incidents", ["status"]) 
    op.create_index("idx_incidents_dedup", "incidents", ["dedup_key"]) 
    op.create_index("idx_incidents_device", "incidents", ["device_id"]) 
    op.create_index("idx_incidents_pon", "incidents", ["pon_id"]) 
    op.create_index("idx_incidents_opened", "incidents", ["opened_at"]) 

    op.create_table(
        "maintenance_windows",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Approved'"), nullable=False),
        sa.Column("pre_check_done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("post_check_done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
    )
    op.create_index("idx_mw_scope", "maintenance_windows", ["scope_type"]) 

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("received_ip", sa.String(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("hmac_valid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
    )
    op.create_index("idx_webhook_source", "webhook_events", ["source"]) 

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_audit_created", "audit_logs", ["created_at"]) 


def downgrade():
    op.drop_index("idx_audit_created", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("idx_webhook_source", table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index("idx_mw_scope", table_name="maintenance_windows")
    op.drop_table("maintenance_windows")

    op.drop_index("idx_incidents_opened", table_name="incidents")
    op.drop_index("idx_incidents_pon", table_name="incidents")
    op.drop_index("idx_incidents_device", table_name="incidents")
    op.drop_index("idx_incidents_dedup", table_name="incidents")
    op.drop_index("idx_incidents_status", table_name="incidents")
    op.drop_table("incidents")

    op.drop_index("idx_optical_baselines_port", table_name="optical_baselines")
    op.drop_index("idx_optical_baselines_onu", table_name="optical_baselines")
    op.drop_table("optical_baselines")

    op.drop_index("idx_optical_readings_time", table_name="optical_readings")
    op.drop_index("idx_optical_readings_device", table_name="optical_readings")
    op.drop_index("idx_optical_readings_port", table_name="optical_readings")
    op.drop_index("idx_optical_readings_onu", table_name="optical_readings")
    op.drop_table("optical_readings")

    op.drop_index("idx_onus_serial", table_name="onus")
    op.drop_index("idx_onus_port", table_name="onus")
    op.drop_index("idx_onus_device", table_name="onus")
    op.drop_table("onus")

    op.drop_index("idx_ports_device", table_name="ports")
    op.drop_table("ports")

    op.drop_index("idx_devices_ward", table_name="devices")
    op.drop_index("idx_devices_pon", table_name="devices")
    op.drop_index("idx_devices_tenant", table_name="devices")
    op.drop_table("devices")

