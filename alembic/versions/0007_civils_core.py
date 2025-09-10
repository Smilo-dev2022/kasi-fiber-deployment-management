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
        sa.Column("length_m", sa.Numeric(), nullable=True),
        sa.Column("width_mm", sa.Integer(), nullable=True),
        sa.Column("depth_mm", sa.Integer(), nullable=True),
        sa.Column("surface_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Planned'"), nullable=False),
        sa.Column("assigned_team", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("path_geojson", sa.Text(), nullable=True),
    )
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
    )
    op.create_index("idx_civils_photos_segment", "civils_photos", ["segment_id"]) 
    op.create_table(
        "duct_installs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="CASCADE")),
        sa.Column("duct_type", sa.String(), nullable=False),
        sa.Column("count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("rope_drawn", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("mandrel_passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("as_built_label", sa.String(), nullable=True),
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
    )
    op.create_index("idx_reinstatements_segment", "reinstatements", ["segment_id"]) 


def downgrade():
    op.drop_index("idx_reinstatements_segment", table_name="reinstatements")
    op.drop_table("reinstatements")
    op.drop_index("idx_duct_installs_segment", table_name="duct_installs")
    op.drop_table("duct_installs")
    op.drop_index("idx_civils_photos_segment", table_name="civils_photos")
    op.drop_table("civils_photos")
    op.drop_table("trench_segments")

