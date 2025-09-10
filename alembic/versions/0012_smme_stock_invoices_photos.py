from alembic import op
import sqlalchemy as sa


revision = "0012_smme_stock_invoices_photos"
down_revision = "0011_photo_tags_stringing"
branch_labels = None
depends_on = None


def upgrade():
    # SMME users and compliance
    op.create_table(
        "smme_users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
    )
    op.create_index("idx_smme_users_smme", "smme_users", ["smme_id"]) 

    op.create_table(
        "compliance_docs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_compliance_smme", "compliance_docs", ["smme_id"]) 

    # Stock management
    op.create_table(
        "skus",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("min_level", sa.Numeric(12, 3), server_default="0", nullable=False),
        sa.Column("reorder_level", sa.Numeric(12, 3), server_default="0", nullable=False),
    )
    op.create_table(
        "stores",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
    )
    op.create_table(
        "stock_batches",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("skus.id", ondelete="CASCADE"), nullable=False),
        sa.Column("qty", sa.Numeric(12, 3), nullable=False),
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supplier", sa.String(), nullable=True),
    )
    op.create_index("idx_stock_batches_store", "stock_batches", ["store_id"]) 
    op.create_index("idx_stock_batches_sku", "stock_batches", ["sku_id"]) 

    op.create_table(
        "stock_moves",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("skus.id", ondelete="CASCADE"), nullable=False),
        sa.Column("qty", sa.Numeric(12, 3), nullable=False),
        sa.Column("from_store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("asset_code", sa.String(), nullable=True),
        sa.Column("moved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("moved_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_stock_moves_sku", "stock_moves", ["sku_id"]) 
    op.create_index("idx_stock_moves_from", "stock_moves", ["from_store_id"]) 
    op.create_index("idx_stock_moves_to", "stock_moves", ["to_store_id"]) 

    # Invoices
    op.create_table(
        "invoices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Draft'"), nullable=False),
        sa.Column("total_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_invoices_org", "invoices", ["org_id"]) 
    op.create_index("idx_invoices_status", "invoices", ["status"]) 

    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("qty", sa.Numeric(), nullable=False),
        sa.Column("rate_cents", sa.BigInteger(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("source_ref_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_invoice_lines_invoice", "invoice_lines", ["invoice_id"]) 

    # Photo tag dictionary and links
    op.create_table(
        "photo_tags",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("required_for_step", sa.String(), nullable=True),
    )
    op.create_table(
        "photo_tag_links",
        sa.Column("photo_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("photo_tags.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade():
    op.drop_index("idx_invoice_lines_invoice", table_name="invoice_lines")
    op.drop_table("invoice_lines")
    op.drop_index("idx_invoices_status", table_name="invoices")
    op.drop_index("idx_invoices_org", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("idx_stock_moves_to", table_name="stock_moves")
    op.drop_index("idx_stock_moves_from", table_name="stock_moves")
    op.drop_index("idx_stock_moves_sku", table_name="stock_moves")
    op.drop_table("stock_moves")
    op.drop_index("idx_stock_batches_sku", table_name="stock_batches")
    op.drop_index("idx_stock_batches_store", table_name="stock_batches")
    op.drop_table("stock_batches")
    op.drop_table("stores")
    op.drop_table("skus")

    op.drop_index("idx_compliance_smme", table_name="compliance_docs")
    op.drop_table("compliance_docs")
    op.drop_index("idx_smme_users_smme", table_name="smme_users")
    op.drop_table("smme_users")
    op.drop_table("photo_tag_links")
    op.drop_table("photo_tags")

