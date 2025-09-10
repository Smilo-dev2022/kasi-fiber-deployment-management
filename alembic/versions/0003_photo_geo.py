from alembic import op
import sqlalchemy as sa


revision = "0003_photo_geo"
down_revision = "0002_sla_timers"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("photos", sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True))
    op.add_column("photos", sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True))
    op.add_column("photos", sa.Column("taken_ts", sa.DateTime(timezone=True), nullable=True))
    op.add_column("photos", sa.Column("exif_ok", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column(
        "photos",
        sa.Column("within_geofence", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("pons", sa.Column("center_lat", sa.Numeric(9, 6), nullable=True))
    op.add_column("pons", sa.Column("center_lng", sa.Numeric(9, 6), nullable=True))
    op.add_column("pons", sa.Column("geofence_radius_m", sa.Integer(), server_default="200", nullable=False))
    op.create_index("idx_photos_taken_ts", "photos", ["taken_ts"])


def downgrade():
    op.drop_index("idx_photos_taken_ts", table_name="photos")
    op.drop_column("pons", "geofence_radius_m")
    op.drop_column("pons", "center_lng")
    op.drop_column("pons", "center_lat")
    op.drop_column("photos", "within_geofence")
    op.drop_column("photos", "exif_ok")
    op.drop_column("photos", "taken_ts")
    op.drop_column("photos", "gps_lng")
    op.drop_column("photos", "gps_lat")
