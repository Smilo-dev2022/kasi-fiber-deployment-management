from alembic import op
import sqlalchemy as sa


revision = "0012_device_configs"
down_revision = "0011_maintenance_windows"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_configs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("running_config", sa.Text(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("hash_sha256", sa.String(), nullable=False),
    )
    op.create_index("idx_device_configs_device_time", "device_configs", ["device_id", "collected_at"]) 

    op.create_table(
        "golden_templates",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_role", sa.String(), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("policy_regex_deny", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_golden_templates_role", "golden_templates", ["device_role"]) 


def downgrade():
    op.drop_index("idx_golden_templates_role", table_name="golden_templates")
    op.drop_table("golden_templates")
    op.drop_index("idx_device_configs_device_time", table_name="device_configs")
    op.drop_table("device_configs")

