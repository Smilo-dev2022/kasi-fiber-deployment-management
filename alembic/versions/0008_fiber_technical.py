from alembic import op
import sqlalchemy as sa

revision = "0008_fiber_technical"
down_revision = "0007_noc_core"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "splice_closures",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("gps_lat", sa.Numeric(9, 6)),
        sa.Column("gps_lng", sa.Numeric(9, 6)),
        sa.Column("enclosure_type", sa.String()),
        sa.Column("tray_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'Planned'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_splice_closures_pon", "splice_closures", ["pon_id"])

    op.create_table(
        "splice_trays",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="CASCADE")),
        sa.Column("tray_no", sa.Integer(), nullable=False),
        sa.Column("fiber_start", sa.Integer()),
        sa.Column("fiber_end", sa.Integer()),
        sa.Column("splices_planned", sa.Integer()),
        sa.Column("splices_done", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("idx_splice_trays_closure", "splice_trays", ["closure_id"])

    op.create_table(
        "splices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tray_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_trays.id", ondelete="CASCADE")),
        sa.Column("core", sa.Integer(), nullable=False),
        sa.Column("from_cable", sa.String()),
        sa.Column("to_cable", sa.String()),
        sa.Column("loss_db", sa.Numeric(5, 3)),
        sa.Column("method", sa.String()),  # fusion or mechanical
        sa.Column("tech_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("time", sa.DateTime(timezone=True)),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.create_index("idx_splices_tray", "splices", ["tray_id"])

    op.create_table(
        "test_plans",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("link_name", sa.String(), nullable=False),
        sa.Column("from_point", sa.String(), nullable=False),
        sa.Column("to_point", sa.String(), nullable=False),
        sa.Column("wavelength_nm", sa.Integer(), nullable=False),
        sa.Column("max_loss_db", sa.Numeric(5, 2), nullable=False),
        sa.Column("otdr_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("lspm_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_test_plans_pon", "test_plans", ["pon_id"])

    op.create_table(
        "otdr_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_plan_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("test_plans.id", ondelete="CASCADE")),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("vendor", sa.String()),
        sa.Column("wavelength_nm", sa.Integer(), nullable=False),
        sa.Column("total_loss_db", sa.Numeric(5, 2)),
        sa.Column("event_count", sa.Integer()),
        sa.Column("max_splice_loss_db", sa.Numeric(5, 2)),
        sa.Column("back_reflection_db", sa.Numeric(5, 2)),
        sa.Column("tested_at", sa.DateTime(timezone=True)),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_otdr_plan_time", "otdr_results", ["test_plan_id", "tested_at"])

    op.create_table(
        "lspm_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_plan_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("test_plans.id", ondelete="CASCADE")),
        sa.Column("wavelength_nm", sa.Integer(), nullable=False),
        sa.Column("measured_loss_db", sa.Numeric(5, 2), nullable=False),
        sa.Column("margin_db", sa.Numeric(5, 2)),
        sa.Column("tested_at", sa.DateTime(timezone=True)),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_lspm_plan_time", "lspm_results", ["test_plan_id", "tested_at"])


def downgrade():
    op.drop_index("idx_lspm_plan_time", table_name="lspm_results")
    op.drop_table("lspm_results")
    op.drop_index("idx_otdr_plan_time", table_name="otdr_results")
    op.drop_table("otdr_results")
    op.drop_index("idx_test_plans_pon", table_name="test_plans")
    op.drop_table("test_plans")
    op.drop_index("idx_splices_tray", table_name="splices")
    op.drop_table("splices")
    op.drop_index("idx_splice_trays_closure", table_name="splice_trays")
    op.drop_table("splice_trays")
    op.drop_index("idx_splice_closures_pon", table_name="splice_closures")
    op.drop_table("splice_closures")

