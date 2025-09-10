from alembic import op
import sqlalchemy as sa

revision = "0014_stringing_runs"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
	op.create_table(
		"stringing_runs",
		sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
		sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
		sa.Column("meters", sa.Numeric(10, 2), nullable=False),
		sa.Column("from_pole", sa.String(), nullable=True),
		sa.Column("to_pole", sa.String(), nullable=True),
		sa.Column("completed_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
		sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("notes", sa.String(), nullable=True),
	)
	op.create_index("idx_stringing_runs_pon_time", "stringing_runs", ["pon_id", "completed_at"]) 


def downgrade():
	op.drop_index("idx_stringing_runs_pon_time", table_name="stringing_runs")
	op.drop_table("stringing_runs")