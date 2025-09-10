from alembic import op
import sqlalchemy as sa


revision = "0014_geo_maps"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure PostGIS is available
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Geo admin boundaries
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS geo_wards (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          name text NOT NULL,
          geom geometry(MultiPolygon, 4326) NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_wards_geom ON geo_wards USING GIST (geom)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS geo_suburbs (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          name text NOT NULL,
          ward_id uuid REFERENCES geo_wards(id) ON DELETE CASCADE,
          geom geometry(MultiPolygon, 4326) NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_suburbs_geom ON geo_suburbs USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_suburbs_ward ON geo_suburbs(ward_id)")

    # PON polygon geofence
    op.execute("ALTER TABLE pons ADD COLUMN IF NOT EXISTS geofence geometry(Polygon, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pons_geofence ON pons USING GIST (geofence)")

    # Poles (new)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS poles (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          pon_id uuid REFERENCES pons(id) ON DELETE CASCADE,
          code text UNIQUE,
          geom geometry(Point, 4326) NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_poles_geom ON poles USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_poles_pon ON poles(pon_id)")

    # Closures and splitters geometry points
    op.execute("ALTER TABLE splice_closures ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)")
    op.execute(
        "UPDATE splice_closures SET geom = ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326) WHERE geom IS NULL AND gps_lat IS NOT NULL AND gps_lng IS NOT NULL"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_splice_closures_geom ON splice_closures USING GIST (geom)")

    op.execute("ALTER TABLE splitters ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)")
    op.execute(
        "UPDATE splitters SET geom = ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326) WHERE geom IS NULL AND gps_lat IS NOT NULL AND gps_lng IS NOT NULL"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_splitters_geom ON splitters USING GIST (geom)")

    # Cable register geometry lines
    op.execute("ALTER TABLE cable_register ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326)")
    op.execute("ALTER TABLE cable_register ADD COLUMN IF NOT EXISTS type text")
    op.execute("ALTER TABLE cable_register ADD COLUMN IF NOT EXISTS chainage_m numeric")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cable_geom ON cable_register USING GIST (geom)")

    # Incidents point geometry
    op.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_incidents_geom ON incidents USING GIST (geom)")

    # Live user GPS traces
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_locations (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id uuid NOT NULL,
          geom geometry(Point, 4326) NOT NULL,
          ts timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_locations_geom ON user_locations USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_user_locations_user_ts ON user_locations(user_id, ts DESC)")


def downgrade():
    # Drop created indexes and columns/tables (best-effort)
    op.execute("DROP INDEX IF EXISTS idx_user_locations_user_ts")
    op.execute("DROP INDEX IF EXISTS idx_user_locations_geom")
    op.execute("DROP TABLE IF EXISTS user_locations")

    op.execute("DROP INDEX IF EXISTS idx_incidents_geom")
    op.execute("ALTER TABLE incidents DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_cable_geom")
    op.execute("ALTER TABLE cable_register DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_splitters_geom")
    op.execute("ALTER TABLE splitters DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_splice_closures_geom")
    op.execute("ALTER TABLE splice_closures DROP COLUMN IF EXISTS geom")

    op.execute("DROP INDEX IF EXISTS idx_poles_pon")
    op.execute("DROP INDEX IF EXISTS idx_poles_geom")
    op.execute("DROP TABLE IF EXISTS poles")

    op.execute("DROP INDEX IF EXISTS idx_pons_geofence")
    op.execute("ALTER TABLE pons DROP COLUMN IF EXISTS geofence")

    op.execute("DROP INDEX IF EXISTS idx_geo_suburbs_ward")
    op.execute("DROP INDEX IF EXISTS idx_geo_suburbs_geom")
    op.execute("DROP TABLE IF EXISTS geo_suburbs")

    op.execute("DROP INDEX IF EXISTS idx_geo_wards_geom")
    op.execute("DROP TABLE IF EXISTS geo_wards")

