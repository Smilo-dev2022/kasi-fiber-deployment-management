from alembic import op
import sqlalchemy as sa

revision = "0004_assets_qr"
down_revision = "0003_photo_geo"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assets",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("sku", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'In Store'"), nullable=False),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id")),
        # issued_to is optional and may reference a user; omit FK to avoid dependency on users table
        sa.Column("issued_to", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Add column only if stock_issues table exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("stock_issues"):
        op.add_column("stock_issues", sa.Column("asset_code", sa.String(), nullable=True))
    op.add_column("photos", sa.Column("asset_code", sa.String(), nullable=True))
    op.create_index("idx_assets_code", "assets", ["code"]) 
    op.create_index("idx_assets_status", "assets", ["status"]) 


def downgrade():
    op.drop_index("idx_assets_status", table_name="assets")
    op.drop_index("idx_assets_code", table_name="assets")
    op.drop_column("photos", "asset_code")
    op.drop_column("stock_issues", "asset_code")
    op.drop_table("assets")

