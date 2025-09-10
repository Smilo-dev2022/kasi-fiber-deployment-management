from alembic import op
import sqlalchemy as sa


revision = "0014_now_features"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    # Stringing runs
    op.create_table(
        "stringing_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("team_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("meters", sa.Numeric(10, 2), nullable=False),
        sa.Column("brackets", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dead_ends", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tensioners", sa.Integer(), server_default="0", nullable=False),
        sa.Column("start_ts", sa.DateTime(timezone=True)),
        sa.Column("end_ts", sa.DateTime(timezone=True)),
        sa.Column("photos_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("qc_passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_stringing_pon", "stringing_runs", ["pon_id"]) 

    # SMMEs and compliance
    op.create_table(
        "smmes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("reg_no", sa.String()),
        sa.Column("tax_no", sa.String()),
        sa.Column("bbee_level", sa.String()),
        sa.Column("contact_name", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "smme_users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("role", sa.String(), nullable=False),
        sa.UniqueConstraint("smme_id", "user_id", name="uq_smme_user"),
    )
    op.create_table(
        "compliance_docs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id", ondelete="CASCADE")),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_compliance_smme", "compliance_docs", ["smme_id"]) 

    # Stock master and movements (project stock, separate from spares)
    op.create_table(
        "skus",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("min_level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reorder_level", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "stock_batches",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("skus.id", ondelete="CASCADE")),
        sa.Column("store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE")),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("supplier", sa.String()),
        sa.Column("note", sa.String()),
    )
    op.create_index("idx_batches_store_sku", "stock_batches", ["store_id", "sku_id"]) 
    op.create_table(
        "stock_moves",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("skus.id", ondelete="CASCADE")),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("from_store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id")),
        sa.Column("to_store_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id")),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id")),
        sa.Column("asset_code", sa.String()),
        sa.Column("moved_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("moved_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("note", sa.String()),
    )
    op.create_index("idx_moves_sku_time", "stock_moves", ["sku_id", "moved_at"]) 

    # Invoices
    op.create_table(
        "invoices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Draft'"), nullable=False),
        sa.Column("total_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
    )
    op.create_index("idx_invoices_org", "invoices", ["org_id", "status"]) 
    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE")),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id")),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("qty", sa.Numeric(12, 2), nullable=False),
        sa.Column("rate_cents", sa.BigInteger(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("source_ref_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_inv_lines_invoice", "invoice_lines", ["invoice_id"]) 

    # Photo tags
    op.create_table(
        "photo_tags",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("required_for_step", sa.String(), nullable=True),
    )
    op.create_table(
        "photo_tag_links",
        sa.Column("photo_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("photo_tags.id", ondelete="CASCADE"), primary_key=True),
    )

    # Seed common tags
    op.execute(
        """
        insert into photo_tags (id, name, required_for_step) values
          (gen_random_uuid(), 'Dig', 'PolePlanting'),
          (gen_random_uuid(), 'Plant', 'PolePlanting'),
          (gen_random_uuid(), 'CA_Measurements', 'CAC'),
          (gen_random_uuid(), 'StringingStart', 'Stringing'),
          (gen_random_uuid(), 'Brackets', 'Stringing'),
          (gen_random_uuid(), 'Tension', 'Stringing'),
          (gen_random_uuid(), 'DeadEnds', 'Stringing'),
          (gen_random_uuid(), 'Completion', 'Stringing')
        on conflict (name) do nothing
        """
    )


def downgrade():
    op.drop_table("photo_tag_links")
    op.drop_table("photo_tags")
    op.drop_index("idx_inv_lines_invoice", table_name="invoice_lines")
    op.drop_table("invoice_lines")
    op.drop_index("idx_invoices_org", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("idx_moves_sku_time", table_name="stock_moves")
    op.drop_table("stock_moves")
    op.drop_index("idx_batches_store_sku", table_name="stock_batches")
    op.drop_table("stock_batches")
    op.drop_table("skus")
    op.drop_index("idx_compliance_smme", table_name="compliance_docs")
    op.drop_table("compliance_docs")
    op.drop_table("smme_users")
    op.drop_table("smmes")
    op.drop_index("idx_stringing_pon", table_name="stringing_runs")
    op.drop_table("stringing_runs")

