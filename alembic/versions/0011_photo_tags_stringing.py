from alembic import op
import sqlalchemy as sa


revision = "0011_photo_tags_stringing"
down_revision = "0010_certificate_acceptance"
branch_labels = None
depends_on = None


def upgrade():
    # Photo tags using simple array to keep lightweight for now
    op.add_column("photos", sa.Column("tags", sa.ARRAY(sa.String()), server_default=sa.text("'{}'"), nullable=False))

    # Stringing runs
    op.create_table(
        "stringing_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("meters", sa.Numeric(8, 2), nullable=False),
        sa.Column("brackets", sa.Integer(), nullable=True),
        sa.Column("dead_ends", sa.Integer(), nullable=True),
        sa.Column("tensioners", sa.Integer(), nullable=True),
        sa.Column("start_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("photos_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("qc_passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_stringing_runs_pon", "stringing_runs", ["pon_id"]) 


def downgrade():
    op.drop_index("idx_stringing_runs_pon", table_name="stringing_runs")
    op.drop_table("stringing_runs")
    op.drop_column("photos", "tags")

