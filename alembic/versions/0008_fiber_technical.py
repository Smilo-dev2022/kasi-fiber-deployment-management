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
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("enclosure_type", sa.String(), nullable=True),
        sa.Column("tray_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Planned'"), nullable=False),
    )
    op.create_index("idx_splice_closures_pon", "splice_closures", ["pon_id"])
    op.create_index("idx_splice_closures_status", "splice_closures", ["status"])

    op.create_table(
        "splice_trays",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="CASCADE")),
        sa.Column("tray_no", sa.Integer(), nullable=False),
        sa.Column("fiber_start", sa.Integer(), nullable=True),
        sa.Column("fiber_end", sa.Integer(), nullable=True),
        sa.Column("splices_planned", sa.Integer(), nullable=True),
        sa.Column("splices_done", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("idx_splice_trays_closure", "splice_trays", ["closure_id"])

    op.create_table(
        "splices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tray_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_trays.id", ondelete="CASCADE")),
        sa.Column("core", sa.Integer(), nullable=False),
        sa.Column("from_cable", sa.String(), nullable=True),
        sa.Column("to_cable", sa.String(), nullable=True),
        sa.Column("loss_db", sa.Numeric(5, 3), nullable=True),
        sa.Column("method", sa.String(), nullable=True),  # fusion or mechanical
        sa.Column("tech_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_splices_tray", "splices", ["tray_id"])
    op.create_index("idx_splices_passed", "splices", ["passed"])

    op.create_table(
        "floating_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("meters", sa.Numeric(10, 2), nullable=True),
        sa.Column("drum_code", sa.String(), nullable=True),
        sa.Column("pull_method", sa.String(), nullable=True),
        sa.Column("lubricant_used", sa.String(), nullable=True),
        sa.Column("start_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("photos_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_floating_runs_pon", "floating_runs", ["pon_id"])
    op.create_index("idx_floating_runs_segment", "floating_runs", ["segment_id"])

    op.create_table(
        "test_plans",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("link_name", sa.String(), nullable=False),
        sa.Column("from_point", sa.String(), nullable=True),
        sa.Column("to_point", sa.String(), nullable=True),
        sa.Column("wavelength_nm", sa.Integer(), nullable=False),
        sa.Column("max_loss_db", sa.Numeric(5, 2), nullable=False),
        sa.Column("otdr_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("lspm_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_test_plans_pon", "test_plans", ["pon_id"])

    op.create_table(
        "otdr_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_plan_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("test_plans.id", ondelete="CASCADE")),
        sa.Column("file_url", sa.String(), nullable=True),
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("wavelength_nm", sa.Integer(), nullable=False),
        sa.Column("total_loss_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=True),
        sa.Column("max_splice_loss_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("back_reflection_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_otdr_results_plan", "otdr_results", ["test_plan_id"])
    op.create_index("idx_otdr_results_tested", "otdr_results", ["tested_at"])

    op.create_table(
        "lspm_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_plan_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("test_plans.id", ondelete="CASCADE")),
        sa.Column("wavelength_nm", sa.Integer(), nullable=False),
        sa.Column("measured_loss_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("margin_db", sa.Numeric(5, 2), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_lspm_results_plan", "lspm_results", ["test_plan_id"])
    op.create_index("idx_lspm_results_tested", "lspm_results", ["tested_at"])

    op.create_table(
        "connector_inspects",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("port", sa.String(), nullable=True),
        sa.Column("microscope_photo_url", sa.String(), nullable=True),
        sa.Column("grade", sa.String(), nullable=True),
        sa.Column("cleaned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("retest_grade", sa.String(), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_connector_inspects_closure", "connector_inspects", ["closure_id"])
    op.create_index("idx_connector_inspects_device", "connector_inspects", ["device_id"])
    op.create_index("idx_connector_inspects_tested", "connector_inspects", ["tested_at"])

    op.create_table(
        "cable_register",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("cable_code", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("length_m", sa.Integer(), nullable=True),
        sa.Column("drum_code", sa.String(), nullable=True),
        sa.Column("installed_m", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("idx_cable_register_pon", "cable_register", ["pon_id"])

    op.create_table(
        "test_photos",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("taken_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exif_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("within_geofence", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
    )
    op.create_index("idx_test_photos_entity", "test_photos", ["entity_type", "entity_id"])


def downgrade():
    op.drop_index("idx_test_photos_entity", table_name="test_photos")
    op.drop_table("test_photos")

    op.drop_index("idx_cable_register_pon", table_name="cable_register")
    op.drop_table("cable_register")

    op.drop_index("idx_connector_inspects_tested", table_name="connector_inspects")
    op.drop_index("idx_connector_inspects_device", table_name="connector_inspects")
    op.drop_index("idx_connector_inspects_closure", table_name="connector_inspects")
    op.drop_table("connector_inspects")

    op.drop_index("idx_lspm_results_tested", table_name="lspm_results")
    op.drop_index("idx_lspm_results_plan", table_name="lspm_results")
    op.drop_table("lspm_results")

    op.drop_index("idx_otdr_results_tested", table_name="otdr_results")
    op.drop_index("idx_otdr_results_plan", table_name="otdr_results")
    op.drop_table("otdr_results")

    op.drop_index("idx_test_plans_pon", table_name="test_plans")
    op.drop_table("test_plans")

    op.drop_index("idx_floating_runs_segment", table_name="floating_runs")
    op.drop_index("idx_floating_runs_pon", table_name="floating_runs")
    op.drop_table("floating_runs")

    op.drop_index("idx_splices_passed", table_name="splices")
    op.drop_index("idx_splices_tray", table_name="splices")
    op.drop_table("splices")

    op.drop_index("idx_splice_trays_closure", table_name="splice_trays")
    op.drop_table("splice_trays")

    op.drop_index("idx_splice_closures_status", table_name="splice_closures")
    op.drop_index("idx_splice_closures_pon", table_name="splice_closures")
    op.drop_table("splice_closures")

