from alembic import op
import sqlalchemy as sa


revision = "0008_noc_devices_incidents_optical"
down_revision = "0007_civils_core"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "devices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("serial", sa.String(), nullable=True),
        sa.Column("mgmt_ip", sa.String(), nullable=True),
        sa.Column("site", sa.String(), nullable=True),
        sa.Column("tenant", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
    )
    op.create_index("idx_devices_serial", "devices", ["serial"], unique=False)
    op.create_index("idx_devices_mgmt_ip", "devices", ["mgmt_ip"], unique=False)

    op.create_table(
        "incidents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="Open"),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_response_min", sa.Integer(), nullable=True),
        sa.Column("sla_restore_min", sa.Integer(), nullable=True),
        sa.Column("breached_response", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("breached_restore", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("root_cause", sa.String(), nullable=True),
        sa.Column("fix_code", sa.String(), nullable=True),
        sa.Column("close_notes", sa.String(), nullable=True),
        sa.Column("close_photo_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("photos.id"), nullable=True),
    )
    op.create_index("idx_incidents_opened_at", "incidents", ["opened_at"], unique=False)
    op.create_index("idx_incidents_status", "incidents", ["status"], unique=False)
    op.create_index("idx_incidents_severity", "incidents", ["severity"], unique=False)

    op.create_table(
        "optical_readings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("onu_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("port_name", sa.String(), nullable=True),
        sa.Column("direction", sa.String(), nullable=True),
        sa.Column("dBm", sa.Numeric(5, 2), nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_optical_taken_at", "optical_readings", ["taken_at"], unique=False)
    op.create_index("idx_optical_pon", "optical_readings", ["pon_id"], unique=False)
    op.create_index("idx_optical_device", "optical_readings", ["device_id"], unique=False)


def downgrade():
    op.drop_index("idx_optical_device", table_name="optical_readings")
    op.drop_index("idx_optical_pon", table_name="optical_readings")
    op.drop_index("idx_optical_taken_at", table_name="optical_readings")
    op.drop_table("optical_readings")

    op.drop_index("idx_incidents_severity", table_name="incidents")
    op.drop_index("idx_incidents_status", table_name="incidents")
    op.drop_index("idx_incidents_opened_at", table_name="incidents")
    op.drop_table("incidents")

    op.drop_index("idx_devices_mgmt_ip", table_name="devices")
    op.drop_index("idx_devices_serial", table_name="devices")
    op.drop_table("devices")

