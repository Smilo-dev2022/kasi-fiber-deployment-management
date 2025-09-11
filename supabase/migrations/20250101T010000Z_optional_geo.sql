-- Optional schema creation: creates geo_wards and geo_suburbs if missing.
CREATE EXTENSION IF NOT EXISTS postgis;

DO $$
BEGIN
  IF to_regclass('public.geo_wards') IS NULL THEN
    CREATE TABLE public.geo_wards (
      id   text,
      name text,
      geom bytea
    );
  END IF;
  IF to_regclass('public.geo_suburbs') IS NULL THEN
    CREATE TABLE public.geo_suburbs (
      id      text,
      name    text,
      ward_id text,
      geom    bytea
    );
  END IF;
END$$;

