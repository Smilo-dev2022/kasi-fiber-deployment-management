from alembic import op
import sqlalchemy as sa


revision = "0011_maintenance_windows"
down_revision = "0010_topology_core"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maint_windows",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("target_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_maint_windows_scope_target", "maint_windows", ["scope", "target_id"]) 
    op.create_index("idx_maint_windows_time", "maint_windows", ["start_at", "end_at"]) 


def downgrade():
    op.drop_index("idx_maint_windows_time", table_name="maint_windows")
    op.drop_index("idx_maint_windows_scope_target", table_name="maint_windows")
    op.drop_table("maint_windows")

