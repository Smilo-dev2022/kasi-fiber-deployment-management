-- Backfill geometry JSON across various tables, conditionally.
-- This script is idempotent and skips steps if tables/columns are missing.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Allow caller to set a projected SRID for easting/northing via a GUC.
-- Example: psql "$DATABASE_URL" -c "set app.srid='2054';" -f backfill_geoms.sql
-- Defaults to 2054 if not provided.
DO $$ BEGIN PERFORM set_config('app.srid', current_setting('app.srid', true), true); EXCEPTION WHEN others THEN NULL; END $$;

-- Helper to fetch SRID from GUC or fallback
CREATE OR REPLACE FUNCTION public._get_app_srid() RETURNS integer LANGUAGE plpgsql AS $$
DECLARE v integer; BEGIN v := COALESCE(NULLIF(current_setting('app.srid', true), '')::int, 2054); RETURN v; END $$;

-- Poles: lat/lng -> geom_geojson
DO $$
BEGIN
  IF to_regclass('public.poles') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='poles' AND column_name='geom_geojson') THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='poles' AND column_name='gps_lat')
       AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='poles' AND column_name='gps_lng') THEN
      EXECUTE $$
        UPDATE public.poles
        SET geom_geojson = ST_AsGeoJSON(ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326))::jsonb
        WHERE geom_geojson IS NULL AND gps_lat IS NOT NULL AND gps_lng IS NOT NULL;$$;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='poles' AND column_name='easting')
       AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='poles' AND column_name='northing') THEN
      EXECUTE format(
        $$UPDATE public.poles
          SET geom_geojson = ST_AsGeoJSON(
            ST_Transform(ST_SetSRID(ST_MakePoint(easting, northing), %s), 4326)
          )::jsonb
          WHERE geom_geojson IS NULL AND easting IS NOT NULL AND northing IS NOT NULL;$$,
        public._get_app_srid()
      );
    END IF;
  END IF;
END$$;

-- Closures: lat/lng and projected variants
DO $$
BEGIN
  IF to_regclass('public.closures') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='closures' AND column_name='geom_geojson') THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='closures' AND column_name='gps_lat')
       AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='closures' AND column_name='gps_lng') THEN
      EXECUTE $$
        UPDATE public.closures
        SET geom_geojson = ST_AsGeoJSON(ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326))::jsonb
        WHERE geom_geojson IS NULL AND gps_lat IS NOT NULL AND gps_lng IS NOT NULL;$$;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='closures' AND column_name='easting')
       AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='closures' AND column_name='northing') THEN
      EXECUTE format(
        $$UPDATE public.closures
          SET geom_geojson = ST_AsGeoJSON(
            ST_Transform(ST_SetSRID(ST_MakePoint(easting, northing), %s), 4326)
          )::jsonb
          WHERE geom_geojson IS NULL AND easting IS NOT NULL AND northing IS NOT NULL;$$,
        public._get_app_srid()
      );
    END IF;
  END IF;
END$$;

-- Cable register: WKT path -> geom_geojson
DO $$
BEGIN
  IF to_regclass('public.cable_register') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_register' AND column_name='geom_geojson') THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_register' AND column_name='path_wkt') THEN
      EXECUTE $$
        UPDATE public.cable_register
          SET geom_geojson = ST_AsGeoJSON(ST_SetSRID(ST_GeomFromText(path_wkt), 4326))::jsonb
          WHERE geom_geojson IS NULL AND path_wkt IS NOT NULL;$$;
    END IF;
  END IF;
END$$;

-- Cable register: build lines from points table cable_points(cable_id, seq, lng, lat)
DO $$
BEGIN
  IF to_regclass('public.cable_points') IS NOT NULL
     AND to_regclass('public.cable_register') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_points' AND column_name='cable_id')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_points' AND column_name='seq')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_points' AND column_name='lng')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_points' AND column_name='lat')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='cable_register' AND column_name='geom_geojson') THEN
    EXECUTE $$
      WITH lines AS (
        SELECT cable_id,
               ST_MakeLine(ST_SetSRID(ST_MakePoint(lng, lat),4326) ORDER BY seq) AS geom
        FROM public.cable_points
        GROUP BY cable_id
      )
      UPDATE public.cable_register c
      SET geom_geojson = ST_AsGeoJSON(l.geom)::jsonb
      FROM lines l
      WHERE c.id = l.cable_id AND c.geom_geojson IS NULL;$$;
  END IF;
END$$;

-- Cleanup helper function (optional to keep)
-- DROP FUNCTION public._get_app_srid();

