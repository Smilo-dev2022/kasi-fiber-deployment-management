from alembic import op
import sqlalchemy as sa


revision = "0007_noc_core"
down_revision = "0006_rates_paysheets"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "devices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "pon_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pons.id", ondelete="SET NULL"),
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),  # OLT, ONT, SWITCH, ROUTER, SPLITTER, UPS
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("serial", sa.String(), nullable=True),
        sa.Column("mgmt_ip", sa.String(), nullable=True),
        sa.Column("site", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_devices_role", "devices", ["role"])
    op.create_index("idx_devices_pon", "devices", ["pon_id"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "pon_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pons.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "device_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
        ),
        sa.Column("severity", sa.String(), nullable=False),  # P1, P2, P3, P4
        sa.Column("category", sa.String(), nullable=False),  # Power, Optical, Link, Device, Capacity
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Open'"), nullable=False),  # Open, Acknowledged, Resolved, Closed
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ack_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("root_cause", sa.String(), nullable=True),
        sa.Column("fix_code", sa.String(), nullable=True),
        sa.Column("nms_ref", sa.String(), nullable=True),
    )
    op.create_index("idx_incidents_status", "incidents", ["status"])
    op.create_index("idx_incidents_device", "incidents", ["device_id"])
    op.create_index("idx_incidents_severity_opened", "incidents", ["severity", "opened_at"])

    op.create_table(
        "optical_readings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "pon_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pons.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "device_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
        ),
        sa.Column("port", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),  # RX, TX
        sa.Column("dbm", sa.Numeric(6, 2), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_optical_device_time", "optical_readings", ["device_id", "read_at"])


def downgrade():
    op.drop_index("idx_optical_device_time", table_name="optical_readings")
    op.drop_table("optical_readings")
    op.drop_index("idx_incidents_device", table_name="incidents")
    op.drop_index("idx_incidents_status", table_name="incidents")
    op.drop_index("idx_incidents_severity_opened", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("idx_devices_pon", table_name="devices")
    op.drop_index("idx_devices_role", table_name="devices")
    op.drop_table("devices")

