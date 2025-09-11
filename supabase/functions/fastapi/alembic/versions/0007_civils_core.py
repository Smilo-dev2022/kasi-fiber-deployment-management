from alembic import op
import sqlalchemy as sa


revision = "0007_civils_core"
down_revision = "0006_rates_paysheets"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "trench_segments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("start_gps", sa.String(), nullable=True),
        sa.Column("end_gps", sa.String(), nullable=True),
        sa.Column("polyline", sa.Text(), nullable=True),
        sa.Column("length_m", sa.Numeric(), nullable=True),
        sa.Column("width_mm", sa.Integer(), nullable=True),
        sa.Column("depth_mm", sa.Integer(), nullable=True),
        sa.Column("surface_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Planned'"), nullable=False),
        sa.Column("assigned_team", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_trench_segments_pon", "trench_segments", ["pon_id"]) 
    op.create_index("idx_trench_segments_status", "trench_segments", ["status"]) 

    op.create_table(
        "civils_photos",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("taken_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exif_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("within_geofence", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_civils_photos_segment", "civils_photos", ["segment_id"]) 
    op.create_index("idx_civils_photos_kind", "civils_photos", ["kind"]) 

    op.create_table(
        "civils_tests",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="CASCADE")),
        sa.Column("test_type", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("lab_ref", sa.String(), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_civils_tests_segment", "civils_tests", ["segment_id"]) 
    op.create_index("idx_civils_tests_type", "civils_tests", ["test_type"]) 

    op.create_table(
        "chambers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("depth_mm", sa.Integer(), nullable=True),
        sa.Column("build_status", sa.String(), server_default=sa.text("'Planned'"), nullable=False),
        sa.Column("photos_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_chambers_pon", "chambers", ["pon_id"]) 
    op.create_index("idx_chambers_build_status", "chambers", ["build_status"]) 

    op.create_table(
        "duct_installs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="CASCADE")),
        sa.Column("duct_type", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("rope_drawn", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("mandrel_passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("as_built_label", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_duct_installs_segment", "duct_installs", ["segment_id"]) 

    op.create_table(
        "reinstatements",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="CASCADE")),
        sa.Column("surface_type", sa.String(), nullable=False),
        sa.Column("area_m2", sa.Numeric(), nullable=True),
        sa.Column("method", sa.String(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("signed_off_by", sa.String(), nullable=True),
        sa.Column("signed_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_reinstatements_segment", "reinstatements", ["segment_id"]) 
    op.create_index("idx_reinstatements_passed", "reinstatements", ["passed"]) 

    op.create_table(
        "traffic_controls",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("permit_no", sa.String(), nullable=True),
        sa.Column("method_statement_url", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("daily_sign_off", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_traffic_controls_pon", "traffic_controls", ["pon_id"]) 


def downgrade():
    op.drop_index("idx_traffic_controls_pon", table_name="traffic_controls")
    op.drop_table("traffic_controls")

    op.drop_index("idx_reinstatements_passed", table_name="reinstatements")
    op.drop_index("idx_reinstatements_segment", table_name="reinstatements")
    op.drop_table("reinstatements")

    op.drop_index("idx_duct_installs_segment", table_name="duct_installs")
    op.drop_table("duct_installs")

    op.drop_index("idx_chambers_build_status", table_name="chambers")
    op.drop_index("idx_chambers_pon", table_name="chambers")
    op.drop_table("chambers")

    op.drop_index("idx_civils_tests_type", table_name="civils_tests")
    op.drop_index("idx_civils_tests_segment", table_name="civils_tests")
    op.drop_table("civils_tests")

    op.drop_index("idx_civils_photos_kind", table_name="civils_photos")
    op.drop_index("idx_civils_photos_segment", table_name="civils_photos")
    op.drop_table("civils_photos")

    op.drop_index("idx_trench_segments_status", table_name="trench_segments")
    op.drop_index("idx_trench_segments_pon", table_name="trench_segments")
    op.drop_table("trench_segments")

