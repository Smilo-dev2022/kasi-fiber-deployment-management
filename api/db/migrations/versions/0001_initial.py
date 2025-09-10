"""initial tables

Revision ID: 0001
Revises: 
Create Date: 2025-09-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    op.create_table(
        "smme",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "pon",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pon_number", sa.String(length=50), nullable=False),
        sa.Column("ward", sa.String(length=100), nullable=True),
        sa.Column("street_area", sa.String(length=255), nullable=True),
        sa.Column("homes_passed", sa.Integer(), nullable=True),
        sa.Column("poles_planned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("poles_planted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cac_passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stringing_done", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("photos_uploaded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Not Started"),
        sa.Column("smme_id", sa.Integer(), sa.ForeignKey("smme.id"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_pon_pon_number", "pon", ["pon_number"], unique=True)
    op.create_index("ix_pon_status", "pon", ["status"], unique=False)
    op.create_index("ix_pon_smme_id", "pon", ["smme_id"], unique=False)

    op.create_table(
        "task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pon_id", sa.Integer(), sa.ForeignKey("pon.id"), nullable=False),
        sa.Column("step", sa.String(length=50), nullable=False),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("smme_id", sa.Integer(), sa.ForeignKey("smme.id"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_task_pon_id", "task", ["pon_id"], unique=False)

    op.create_table(
        "photo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pon_id", sa.Integer(), sa.ForeignKey("pon.id"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("task.id"), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("taken_at", sa.DateTime(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
    )
    op.create_index("ix_photo_pon_id", "photo", ["pon_id"], unique=False)

    op.create_table(
        "caccheck",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pon_id", sa.Integer(), sa.ForeignKey("pon.id"), nullable=False),
        sa.Column("pole_number", sa.String(), nullable=False),
        sa.Column("pole_length_m", sa.Float(), nullable=False),
        sa.Column("depth_m", sa.Float(), nullable=False),
        sa.Column("tag_height_m", sa.Float(), nullable=False),
        sa.Column("hook_position", sa.String(length=100), nullable=True),
        sa.Column("alignment_ok", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("comments", sa.String(length=1000), nullable=True),
        sa.Column("checked_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_cac_pon_id", "caccheck", ["pon_id"], unique=False)

    op.create_table(
        "stringingrun",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pon_id", sa.Integer(), sa.ForeignKey("pon.id"), nullable=False),
        sa.Column("meters", sa.Float(), nullable=False, server_default="0"),
        sa.Column("brackets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dead_ends", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tensioner", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stringing_pon_id", "stringingrun", ["pon_id"], unique=False)

    op.create_table(
        "stockitem",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit", sa.String(length=10), nullable=False),
        sa.Column("on_hand", sa.Float(), nullable=False, server_default="0"),
        sa.CheckConstraint("on_hand >= 0", name="ck_stockitem_on_hand_nonnegative"),
    )
    op.create_index("ix_stockitem_sku", "stockitem", ["sku"], unique=True)

    op.create_table(
        "stockissue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("stockitem.id"), nullable=False),
        sa.Column("pon_id", sa.Integer(), sa.ForeignKey("pon.id"), nullable=True),
        sa.Column("issued_to", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stockissue_item_id", "stockissue", ["item_id"], unique=False)

    op.create_table(
        "invoice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pon_id", sa.Integer(), sa.ForeignKey("pon.id"), nullable=False),
        sa.Column("smme_id", sa.Integer(), sa.ForeignKey("smme.id"), nullable=True),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Draft"),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_invoice_pon_id", "invoice", ["pon_id"], unique=False)

    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("auditlog")
    op.drop_table("invoice")
    op.drop_table("stockissue")
    op.drop_index("ix_stockitem_sku", table_name="stockitem")
    op.drop_table("stockitem")
    op.drop_table("stringingrun")
    op.drop_table("caccheck")
    op.drop_table("photo")
    op.drop_table("task")
    op.drop_index("ix_pon_smme_id", table_name="pon")
    op.drop_index("ix_pon_status", table_name="pon")
    op.drop_index("ix_pon_pon_number", table_name="pon")
    op.drop_table("pon")
    op.drop_table("smme")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")

