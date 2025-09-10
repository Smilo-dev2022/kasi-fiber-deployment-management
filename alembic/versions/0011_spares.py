from alembic import op
import sqlalchemy as sa


revision = "0011_spares"
down_revision = "0010_topology_maint_configs_spares"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stores",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String()),
    )
    op.create_table(
        "stock_levels",
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("sku", sa.String(), primary_key=True),
        sa.Column("qty", sa.Integer(), nullable=False),
    )
    op.create_table(
        "spare_issues",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="SET NULL")),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL")),
        sa.Column("to_user", sa.dialects.postgresql.UUID(as_uuid=True)),
    )
    op.create_table(
        "spare_returns",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="SET NULL")),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL")),
        sa.Column("by_user", sa.dialects.postgresql.UUID(as_uuid=True)),
    )
    op.execute("ALTER TABLE stores ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE stock_levels ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE spare_issues ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE spare_returns ENABLE ROW LEVEL SECURITY")


def downgrade():
    op.drop_table("spare_returns")
    op.drop_table("spare_issues")
    op.drop_table("stock_levels")
    op.drop_table("stores")

