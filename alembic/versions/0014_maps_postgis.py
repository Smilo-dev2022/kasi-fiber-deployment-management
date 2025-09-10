from alembic import op
import sqlalchemy as sa


revision = "0014_maps_postgis"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Geospatial columns (store as GeoJSON for simplicity; views will cast)
    with op.batch_alter_table("pons") as batch_op:
        batch_op.add_column(sa.Column("geofence", sa.dialects.postgresql.JSONB(), nullable=True))
    with op.batch_alter_table("photos") as batch_op:
        batch_op.add_column(sa.Column("gps_point", sa.dialects.postgresql.JSONB(), nullable=True))

    # Incidents geometry as GeoJSON
    with op.batch_alter_table("incidents") as batch_op:
        batch_op.add_column(sa.Column("geom_geojson", sa.dialects.postgresql.JSONB(), nullable=True))

    # Raw geo layers (geometry in helper tables for speed) - store WKB in BYTEA
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

    # Optional asset geometry on core tables if present in schema
    for tbl in ("poles", "closures", "cable_register"):
        try:
            with op.batch_alter_table(tbl) as batch_op:
                batch_op.add_column(sa.Column("geom_geojson", sa.dialects.postgresql.JSONB(), nullable=True))
        except Exception:
            # Table may not exist in this installation
            pass

    # User locations (for live user pings)
    op.create_table(
        "user_locations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("geom_geojson", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_user_locations_user_time", "user_locations", ["user_id", "ts"])

    # Views to cast GeoJSON to PostGIS geometry for spatial ops
    op.execute(
        """
    CREATE OR REPLACE VIEW v_pons AS
    SELECT p.*, ST_SetSRID(ST_GeomFromGeoJSON(p.geofence::text), 4326) AS geofence_geom
    FROM pons p
    """
    )
    op.execute(
        """
    CREATE OR REPLACE VIEW v_photos AS
    SELECT ph.*, ST_SetSRID(ST_GeomFromGeoJSON(ph.gps_point::text), 4326) AS gps_geom
    FROM photos ph
    """
    )
    op.execute(
        """
    CREATE OR REPLACE VIEW v_incidents AS
    SELECT i.*, ST_SetSRID(ST_GeomFromGeoJSON(i.geom_geojson::text), 4326) AS geom
    FROM incidents i
    """
    )

    # Spatial indexes on helper geometry
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_geo_wards_geom ON geo_wards USING GIST (public.ST_GeomFromWKB(geom))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_geo_suburbs_geom ON geo_suburbs USING GIST (public.ST_GeomFromWKB(geom))"
    )


def downgrade():
    # Views
    op.execute("DROP VIEW IF EXISTS v_incidents")
    op.execute("DROP VIEW IF EXISTS v_photos")
    op.execute("DROP VIEW IF EXISTS v_pons")

    # Tables and columns
    op.drop_index("idx_user_locations_user_time", table_name="user_locations")
    op.drop_table("user_locations")

    try:
        with op.batch_alter_table("cable_register") as batch_op:
            batch_op.drop_column("geom_geojson")
    except Exception:
        pass
    try:
        with op.batch_alter_table("closures") as batch_op:
            batch_op.drop_column("geom_geojson")
    except Exception:
        pass
    try:
        with op.batch_alter_table("poles") as batch_op:
            batch_op.drop_column("geom_geojson")
    except Exception:
        pass

    op.drop_table("geo_suburbs")
    op.drop_table("geo_wards")

    with op.batch_alter_table("incidents") as batch_op:
        batch_op.drop_column("geom_geojson")
    with op.batch_alter_table("photos") as batch_op:
        batch_op.drop_column("gps_point")
    with op.batch_alter_table("pons") as batch_op:
        batch_op.drop_column("geofence")

