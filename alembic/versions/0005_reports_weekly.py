from alembic import op
import sqlalchemy as sa

revision = "0005_reports_weekly"
down_revision = "0004_assets_qr"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_reports_kind", "reports", ["kind"]) 
    op.create_index("idx_reports_period", "reports", ["period_start", "period_end"]) 


def downgrade():
    op.drop_index("idx_reports_period", table_name="reports")
    op.drop_index("idx_reports_kind", table_name="reports")
    op.drop_table("reports")

