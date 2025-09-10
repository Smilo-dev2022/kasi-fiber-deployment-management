from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("create extension if not exists \"uuid-ossp\";")
    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String()),
        sa.Column("email", sa.String(), unique=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
    )
    op.create_table(
        "smmes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("contact_name", sa.String()),
        sa.Column("contact_phone", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
    )
    op.create_table(
        "pons",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_number", sa.String(), nullable=False, unique=True),
        sa.Column("ward", sa.String()),
        sa.Column("street_area", sa.String()),
        sa.Column("homes_passed", sa.Integer(), server_default="0"),
        sa.Column("poles_planned", sa.Integer(), server_default="0"),
        sa.Column("poles_planted", sa.Integer(), server_default="0"),
        sa.Column("cac_passed", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("stringing_done", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("photos_uploaded", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("status", sa.String(), server_default=sa.text("'Not Started'")),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id")),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("step", sa.String(), nullable=False),
        sa.Column("assigned_to", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id")),
        sa.Column("status", sa.String(), server_default=sa.text("'Pending'")),
        sa.Column("notes", sa.String()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "photos",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("task_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL")),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("kind", sa.String()),
        sa.Column("taken_at", sa.DateTime(timezone=True)),
        sa.Column("uploaded_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )
    op.create_table(
        "cac_checks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("pole_number", sa.String()),
        sa.Column("pole_length_m", sa.Numeric()),
        sa.Column("depth_m", sa.Numeric()),
        sa.Column("tag_height_m", sa.Numeric()),
        sa.Column("hook_position", sa.String()),
        sa.Column("alignment_ok", sa.Boolean()),
        sa.Column("comments", sa.String()),
        sa.Column("checked_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("passed", sa.Boolean()),
        sa.Column("checked_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "stringing_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("meters", sa.Numeric()),
        sa.Column("brackets", sa.Integer()),
        sa.Column("dead_ends", sa.Integer()),
        sa.Column("tensioner", sa.Integer()),
        sa.Column("completed_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "stock_items",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku", sa.String(), unique=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("on_hand", sa.Integer(), server_default="0"),
    )
    op.create_table(
        "stock_issues",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("stock_items.id")),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id")),
        sa.Column("issued_to", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id")),
        sa.Column("smme_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("smmes.id")),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Draft'")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    for t in (
        "invoices","stock_issues","stock_items","stringing_runs","cac_checks",
        "photos","tasks","pons","smmes","users"
    ):
        op.drop_table(t)
