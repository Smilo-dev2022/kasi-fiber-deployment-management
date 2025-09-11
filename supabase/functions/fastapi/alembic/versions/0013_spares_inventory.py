from alembic import op
import sqlalchemy as sa


revision = "0013_spares_inventory"
down_revision = "0012_device_configs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stores",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
    )
    op.create_table(
        "stock_levels",
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("sku", sa.String(), primary_key=True),
        sa.Column("qty", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_stock_store", "stock_levels", ["store_id"]) 
    op.create_index("idx_stock_sku", "stock_levels", ["sku"]) 

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("delta_qty", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_stock_movements_store_time", "stock_movements", ["store_id", "created_at"]) 


def downgrade():
    op.drop_index("idx_stock_movements_store_time", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("idx_stock_sku", table_name="stock_levels")
    op.drop_index("idx_stock_store", table_name="stock_levels")
    op.drop_table("stock_levels")
    op.drop_table("stores")

