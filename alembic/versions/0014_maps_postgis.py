from alembic import op
import sqlalchemy as sa


revision = "0014_maps_postgis"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Geospatial columns
    op.add_column("pons", sa.Column("geofence", sa.dialects.postgresql.JSONB(), nullable=True))  # store polygon as GeoJSON; DB view will cast
    op.add_column("photos", sa.Column("gps_point", sa.dialects.postgresql.JSONB(), nullable=True))  # GeoJSON Point
    op.add_column("incidents", sa.Column("geom_geojson", sa.dialects.postgresql.JSONB(), nullable=True))

    # Raw geo layers (geometry in helper tables for speed)
    op.create_table(
        "geo_wards",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("geom", sa.dialects.postgresql.BYTEA(), nullable=False),  # WKB geometry (PostGIS)
    )
    op.create_table(
        "geo_suburbs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ward_id", sa.String(), sa.ForeignKey("geo_wards.id", ondelete="SET NULL")),
        sa.Column("geom", sa.dialects.postgresql.BYTEA(), nullable=False),
    )

    # User locations to capture last known position
    op.create_table(
        "user_locations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("geom_geojson", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_user_locations_user_time", "user_locations", ["user_id", "ts"]) 

    # Asset geometry on core tables (optional, if not already present)
    for tbl in ("poles", "splice_closures", "cable_register"):
        try:
            op.add_column(tbl, sa.Column("geom_geojson", sa.dialects.postgresql.JSONB(), nullable=True))
        except Exception:
            pass

    # Views to cast GeoJSON to PostGIS geometry for spatial ops
    op.execute(
        """
    CREATE OR REPLACE VIEW v_pons AS
    SELECT p.*,
           ST_SetSRID(ST_GeomFromGeoJSON(p.geofence::text), 4326) AS geofence_geom
    FROM pons p
    """
    )
    op.execute(
        """
    CREATE OR REPLACE VIEW v_photos AS
    SELECT ph.*,
           ST_SetSRID(ST_GeomFromGeoJSON(ph.gps_point::text), 4326) AS gps_geom
    FROM photos ph
    """
    )
    op.execute(
        """
    CREATE OR REPLACE VIEW v_incidents AS
    SELECT i.*,
           ST_SetSRID(ST_GeomFromGeoJSON(i.geom_geojson::text), 4326) AS geom
    FROM incidents i
    """
    )

    # Spatial indexes on helper geometry
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_wards_geom ON geo_wards USING GIST (public.ST_GeomFromWKB(geom))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_suburbs_geom ON geo_suburbs USING GIST (public.ST_GeomFromWKB(geom))")


def downgrade():
    op.execute("DROP VIEW IF EXISTS v_incidents")
    op.execute("DROP VIEW IF EXISTS v_photos")
    op.execute("DROP VIEW IF EXISTS v_pons")
    try:
        op.drop_column("cable_register", "geom_geojson")
    except Exception:
        pass
    try:
        op.drop_column("closures", "geom_geojson")
    except Exception:
        pass
    try:
        op.drop_column("poles", "geom_geojson")
    except Exception:
        pass
    op.drop_index("idx_user_locations_user_time", table_name="user_locations")
    op.drop_table("user_locations")
    op.drop_table("geo_suburbs")
    op.drop_table("geo_wards")
    op.drop_column("incidents", "geom_geojson")
    op.drop_column("photos", "gps_point")
    op.drop_column("pons", "geofence")

