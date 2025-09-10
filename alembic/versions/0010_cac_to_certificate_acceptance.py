from alembic import op
import sqlalchemy as sa


revision = "0010_cac_to_certificate_acceptance"
down_revision = "0009_access_ops"
branch_labels = None
depends_on = None


def upgrade():
    # New table
    op.create_table(
        "certificate_acceptance",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pole_number", sa.String(), nullable=True),
        sa.Column("pole_length_m", sa.Numeric(4, 2), nullable=False),
        sa.Column("depth_m", sa.Numeric(3, 2), nullable=False),
        sa.Column("tag_height_m", sa.Numeric(3, 2), nullable=False),
        sa.Column("hook_position", sa.String(), nullable=True),
        sa.Column("alignment_ok", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("comments", sa.String(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("checked_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Data migration from cac_checks if exists
    conn = op.get_bind()
    try:
        conn.execute(sa.text(
            """
            insert into certificate_acceptance (id, pon_id, pole_number, pole_length_m, depth_m, tag_height_m, hook_position, alignment_ok, comments, passed)
            select id, pon_id, pole_number, pole_length_m, depth_m, tag_height_m, hook_position, alignment_ok, comments, passed
            from cac_checks
            """
        ))
    except Exception:
        # Table may not exist in some environments
        pass
    # Drop old table if present
    try:
        op.drop_table("cac_checks")
    except Exception:
        pass


def downgrade():
    # Recreate old table (without checked_by/checked_at)
    op.create_table(
        "cac_checks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pole_number", sa.String(), nullable=True),
        sa.Column("pole_length_m", sa.Numeric(4, 2), nullable=False),
        sa.Column("depth_m", sa.Numeric(3, 2), nullable=False),
        sa.Column("tag_height_m", sa.Numeric(3, 2), nullable=False),
        sa.Column("hook_position", sa.String(), nullable=True),
        sa.Column("alignment_ok", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("comments", sa.String(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        insert into cac_checks (id, pon_id, pole_number, pole_length_m, depth_m, tag_height_m, hook_position, alignment_ok, comments, passed)
        select id, pon_id, pole_number, pole_length_m, depth_m, tag_height_m, hook_position, alignment_ok, comments, passed
        from certificate_acceptance
        """
    ))
    op.drop_table("certificate_acceptance")

