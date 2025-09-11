from alembic import op
import sqlalchemy as sa


revision = "0014_map_postgis"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # PON geofence polygon (keep existing center/radius for compatibility)
    op.execute(
        "ALTER TABLE pons ADD COLUMN IF NOT EXISTS geofence_geom geometry(Polygon, 4326)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pons_geofence_geom ON pons USING GIST(geofence_geom)"
    )

    # Closures point geometry and index; backfill from lat/lng when available
    op.execute(
        "ALTER TABLE splice_closures ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)"
    )
    op.execute(
        "UPDATE splice_closures SET geom = ST_SetSRID(ST_MakePoint(gps_lng::double precision, gps_lat::double precision), 4326) WHERE geom IS NULL AND gps_lat IS NOT NULL AND gps_lng IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_splice_closures_geom ON splice_closures USING GIST(geom)"
    )

    # Cable register lines and metadata
    op.execute(
        "ALTER TABLE cable_register ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326)"
    )
    op.execute("ALTER TABLE cable_register ADD COLUMN IF NOT EXISTS type text")
    op.execute("ALTER TABLE cable_register ADD COLUMN IF NOT EXISTS chainage_m numeric")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cable_register_geom ON cable_register USING GIST(geom)"
    )

    # Incidents point geometry
    op.execute(
        "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_incidents_geom ON incidents USING GIST(geom)"
    )

    # Poles table
    op.create_table(
        "poles",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("geom", sa.types.UserDefinedType(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    # Adjust geometry type for poles (workaround without geoalchemy2)
    op.execute("ALTER TABLE poles ALTER COLUMN geom TYPE geometry(Point, 4326)")
    op.create_index("idx_poles_pon", "poles", ["pon_id"]) 
    op.execute("CREATE INDEX IF NOT EXISTS idx_poles_geom ON poles USING GIST(geom)")

    # Wards and suburbs geometry tables
    op.create_table(
        "geo_wards",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("geom", sa.types.UserDefinedType(), nullable=False),
    )
    op.execute("ALTER TABLE geo_wards ALTER COLUMN geom TYPE geometry(MultiPolygon, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_wards_geom ON geo_wards USING GIST(geom)")

    op.create_table(
        "geo_suburbs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ward_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("geo_wards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("geom", sa.types.UserDefinedType(), nullable=False),
    )
    op.execute("ALTER TABLE geo_suburbs ALTER COLUMN geom TYPE geometry(MultiPolygon, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_suburbs_geom ON geo_suburbs USING GIST(geom)")

    # User live locations
    op.create_table(
        "user_locations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("geom", sa.types.UserDefinedType(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("ALTER TABLE user_locations ALTER COLUMN geom TYPE geometry(Point, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_locations_geom ON user_locations USING GIST(geom)")
    op.create_index("idx_user_locations_ts", "user_locations", ["ts"]) 


def downgrade():
    # Drop new tables and columns (safe order)
    op.drop_index("idx_user_locations_ts", table_name="user_locations")
    op.execute("DROP INDEX IF EXISTS idx_user_locations_geom")
    op.drop_table("user_locations")

    op.execute("DROP INDEX IF EXISTS idx_geo_suburbs_geom")
    op.drop_table("geo_suburbs")
    op.execute("DROP INDEX IF EXISTS idx_geo_wards_geom")
    op.drop_table("geo_wards")

    op.execute("DROP INDEX IF EXISTS idx_poles_geom")
    op.drop_index("idx_poles_pon", table_name="poles")
    op.drop_table("poles")

    op.execute("DROP INDEX IF EXISTS idx_incidents_geom")
    op.execute("ALTER TABLE incidents DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_cable_register_geom")
    op.execute("ALTER TABLE cable_register DROP COLUMN IF EXISTS chainage_m")
    op.execute("ALTER TABLE cable_register DROP COLUMN IF EXISTS type")
    op.execute("ALTER TABLE cable_register DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_splice_closures_geom")
    op.execute("ALTER TABLE splice_closures DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_pons_geofence_geom")
    op.execute("ALTER TABLE pons DROP COLUMN IF EXISTS geofence_geom")

