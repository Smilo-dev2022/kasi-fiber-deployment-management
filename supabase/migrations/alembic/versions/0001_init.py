from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Minimal bootstrap tables that subsequent migrations extend
    op.create_table(
        "pons",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(), nullable=True, server_default=sa.text("'planned'")),
    )
    op.create_table(
        "photos",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id"), nullable=True),
        sa.Column("step", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "smmes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
    )


def downgrade():
    op.drop_table("smmes")
    op.drop_table("tasks")
    op.drop_table("photos")
    op.drop_table("pons")

