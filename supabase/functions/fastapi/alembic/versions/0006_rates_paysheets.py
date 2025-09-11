from alembic import op
import sqlalchemy as sa

revision = "0006_rates_paysheets"
down_revision = "0005_reports_weekly"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rate_cards",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id")),
        sa.Column("step", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("rate_cents", sa.BigInteger(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
    )
    op.create_table(
        "pay_sheets",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id")),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("total_cents", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Draft'"), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
    )
    op.create_table(
        "pay_sheet_lines",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pay_sheet_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pay_sheets.id", ondelete="CASCADE")),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id")),
        sa.Column("step", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("rate_cents", sa.BigInteger(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
    )
    op.create_index("idx_rate_cards_active", "rate_cards", ["active"]) 
    op.create_index("idx_pay_sheets_smme", "pay_sheets", ["smme_id"]) 
    op.create_index("idx_pay_sheet_lines_ps", "pay_sheet_lines", ["pay_sheet_id"]) 


def downgrade():
    op.drop_index("idx_pay_sheet_lines_ps", table_name="pay_sheet_lines")
    op.drop_index("idx_pay_sheets_smme", table_name="pay_sheets")
    op.drop_index("idx_rate_cards_active", table_name="rate_cards")
    op.drop_table("pay_sheet_lines")
    op.drop_table("pay_sheets")
    op.drop_table("rate_cards")

