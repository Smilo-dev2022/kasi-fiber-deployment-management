-- Add geofence to existing PONs where possible.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Option A: center and radius_m columns present
DO $$
BEGIN
  IF to_regclass('public.pons') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='pons' AND column_name='geofence') THEN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='pons' AND column_name='center_lat')
       AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='pons' AND column_name='center_lng')
       AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='pons' AND column_name='radius_m') THEN
      EXECUTE $$
        UPDATE public.pons
        SET geofence = ST_AsGeoJSON(
          ST_Transform(
            ST_Buffer(
              ST_SetSRID(ST_MakePoint(center_lng, center_lat), 4326)::geography,
              radius_m
            )::geometry, 4326)
        )::jsonb
        WHERE geofence IS NULL AND center_lat IS NOT NULL AND center_lng IS NOT NULL AND radius_m IS NOT NULL;$$;
    END IF;

    -- Option B: boundary_wkt column present
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='pons' AND column_name='boundary_wkt') THEN
      EXECUTE $$
        UPDATE public.pons
        SET geofence = ST_AsGeoJSON(ST_SetSRID(ST_GeomFromText(boundary_wkt), 4326))::jsonb
        WHERE geofence IS NULL AND boundary_wkt IS NOT NULL;$$;
    END IF;

    -- Optional simplify for lighter map payloads
    EXECUTE $$
      UPDATE public.pons
      SET geofence = ST_AsGeoJSON(
        ST_SimplifyPreserveTopology(
          ST_SetSRID(ST_GeomFromGeoJSON(geofence::text),4326),
          0.0001
        )
      )::jsonb
      WHERE geofence IS NOT NULL;$$;
  END IF;
END$$;

