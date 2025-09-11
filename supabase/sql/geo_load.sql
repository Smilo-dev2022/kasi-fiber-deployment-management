-- Ensure PostGIS is available
CREATE EXTENSION IF NOT EXISTS postgis;

-- Insert Wards
DO $$
DECLARE
  have_target boolean := (to_regclass('public.geo_wards') IS NOT NULL);
  have_src    boolean := (to_regclass('public.wards_src') IS NOT NULL);
BEGIN
  IF have_target AND have_src THEN
    EXECUTE $$TRUNCATE public.geo_wards;$$;
    EXECUTE $$
      INSERT INTO public.geo_wards(id, name, geom)
      SELECT
        COALESCE(
          to_jsonb(ws)->>'ward_id',
          to_jsonb(ws)->>'code',
          to_jsonb(ws)->>'gid'
        ) AS id,
        COALESCE(
          to_jsonb(ws)->>'ward_name',
          to_jsonb(ws)->>'name',
          to_jsonb(ws)->>'descr'
        ) AS name,
        ST_AsBinary(ws.geom) AS geom
      FROM public.wards_src ws
      WHERE ws.geom IS NOT NULL;$$;

    -- Index for performance
    EXECUTE $$DROP INDEX IF EXISTS public.idx_geo_wards_geom;$$;
    EXECUTE $$CREATE INDEX idx_geo_wards_geom ON public.geo_wards USING GIST (ST_GeomFromWKB(geom));$$;
  END IF;
END$$;

-- Insert Suburbs
DO $$
DECLARE
  have_target boolean := (to_regclass('public.geo_suburbs') IS NOT NULL);
  have_src    boolean := (to_regclass('public.suburbs_src') IS NOT NULL);
BEGIN
  IF have_target AND have_src THEN
    EXECUTE $$TRUNCATE public.geo_suburbs;$$;
    EXECUTE $$
      INSERT INTO public.geo_suburbs(id, name, ward_id, geom)
      SELECT
        COALESCE(
          to_jsonb(ss)->>'suburb_id',
          to_jsonb(ss)->>'gid'
        ) AS id,
        COALESCE(
          to_jsonb(ss)->>'suburb',
          to_jsonb(ss)->>'name'
        ) AS name,
        COALESCE(
          to_jsonb(ss)->>'ward_id',
          to_jsonb(ss)->>'wardcode'
        ) AS ward_id,
        ST_AsBinary(ss.geom) AS geom
      FROM public.suburbs_src ss
      WHERE ss.geom IS NOT NULL;$$;

    -- Index for performance
    EXECUTE $$DROP INDEX IF EXISTS public.idx_geo_suburbs_geom;$$;
    EXECUTE $$CREATE INDEX idx_geo_suburbs_geom ON public.geo_suburbs USING GIST (ST_GeomFromWKB(geom));$$;
  END IF;
END$$;

