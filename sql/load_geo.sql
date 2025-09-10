-- Geo loader for Stats SA wards (2021) and SubPlace (2011)
-- Handles alternate field names and spatial join fallback
-- Requires: PostGIS, source tables `wards_src` and `suburbs_src` loaded via ogr2ogr

SET client_min_messages = WARNING;
SET search_path = public;

-- Ensure PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Destination tables
CREATE TABLE IF NOT EXISTS geo_wards (
  id   text PRIMARY KEY,
  name text,
  geom bytea NOT NULL
);

CREATE TABLE IF NOT EXISTS geo_suburbs (
  id      text PRIMARY KEY,
  name    text,
  ward_id text,
  geom    bytea NOT NULL
);

-- Load wards
TRUNCATE geo_wards;

DO $$
DECLARE
  id_col   text;
  name_col text;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'wards_src'
  ) THEN
    RAISE EXCEPTION 'Source table % not found', 'wards_src';
  END IF;

  -- Determine ID column: prefer ward_id, then code, then wardno
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'ward_id'
  ) THEN id_col := 'ward_id';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'code'
  ) THEN id_col := 'code';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'wardno'
  ) THEN id_col := 'wardno';
  ELSE
    RAISE EXCEPTION 'Could not determine ID column for %', 'wards_src';
  END IF;

  -- Determine NAME column: prefer ward_name, then name, else reuse id
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'ward_name'
  ) THEN name_col := 'ward_name';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'name'
  ) THEN name_col := 'name';
  ELSE name_col := id_col;
  END IF;

  EXECUTE format($f$
    INSERT INTO geo_wards(id, name, geom)
    SELECT %1$s::text, %2$s::text, ST_AsBinary(wkb_geometry)
    FROM wards_src
    WHERE wkb_geometry IS NOT NULL
  $f$, quote_ident(id_col), quote_ident(name_col));
END $$;

-- Load suburbs (SubPlace 2011), with optional spatial join to wards for ward_id
TRUNCATE geo_suburbs;

DO $$
DECLARE
  id_col        text;
  name_col      text;
  ward_col      text;
  wards_id_col  text;
  id_expr       text;
  name_expr     text;
  ward_expr     text;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'suburbs_src'
  ) THEN
    RAISE EXCEPTION 'Source table % not found', 'suburbs_src';
  END IF;

  -- Determine suburb ID column: prefer sp_code, then sub_code, then code, else NULL
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'sp_code'
  ) THEN id_col := 'sp_code';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'sub_code'
  ) THEN id_col := 'sub_code';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'code'
  ) THEN id_col := 'code';
  ELSE id_col := NULL;
  END IF;

  -- Determine suburb NAME column: prefer sp_name, then sub_name, then name, else NULL
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'sp_name'
  ) THEN name_col := 'sp_name';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'sub_name'
  ) THEN name_col := 'sub_name';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'name'
  ) THEN name_col := 'name';
  ELSE name_col := NULL;
  END IF;

  -- Determine ward reference column in suburbs (if any)
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'ward_id'
  ) THEN ward_col := 'ward_id';
  ELSIF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'suburbs_src' AND column_name = 'wardno'
  ) THEN ward_col := 'wardno';
  ELSE ward_col := NULL;
  END IF;

  IF ward_col IS NOT NULL THEN
    -- Direct load when a ward reference exists in suburbs
    id_expr := COALESCE(format('%s::text', quote_ident(id_col)), 'gid::text');
    name_expr := CASE
      WHEN name_col IS NOT NULL THEN format('%s::text', quote_ident(name_col))
      WHEN id_col IS NOT NULL THEN format('%s::text', quote_ident(id_col))
      ELSE 'gid::text'
    END;
    ward_expr := format('%s::text', quote_ident(ward_col));

    EXECUTE format($f$
      INSERT INTO geo_suburbs(id, name, ward_id, geom)
      SELECT %1$s, %2$s, %3$s, ST_AsBinary(wkb_geometry)
      FROM suburbs_src
      WHERE wkb_geometry IS NOT NULL
    $f$, id_expr, name_expr, ward_expr);
  ELSE
    -- Spatial join to wards when suburbs lack ward reference
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = 'wards_src'
    ) THEN
      RAISE EXCEPTION 'Source table % not found (required for spatial join)', 'wards_src';
    END IF;

    -- Determine wards ID column for join result
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'ward_id'
    ) THEN wards_id_col := 'ward_id';
    ELSIF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'code'
    ) THEN wards_id_col := 'code';
    ELSIF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'wards_src' AND column_name = 'wardno'
    ) THEN wards_id_col := 'wardno';
    ELSE
      RAISE EXCEPTION 'Could not determine ID column for %', 'wards_src';
    END IF;

    id_expr := COALESCE(format('%s::text', quote_ident(id_col)), 'gid::text');
    name_expr := CASE
      WHEN name_col IS NOT NULL THEN format('%s::text', quote_ident(name_col))
      WHEN id_col IS NOT NULL THEN format('%s::text', quote_ident(id_col))
      ELSE 'gid::text'
    END;

    EXECUTE format($f$
      WITH sub AS (
        SELECT gid,
               ST_CollectionExtract(wkb_geometry, 3) AS g,
               %1$s AS sid,
               %2$s AS sname
        FROM suburbs_src
      ),
      ward AS (
        SELECT %3$s::text AS wid, wkb_geometry
        FROM wards_src
      )
      INSERT INTO geo_suburbs(id, name, ward_id, geom)
      SELECT
        COALESCE(sub.sid, sub.gid::text),
        COALESCE(sub.sname, sub.sid, sub.gid::text),
        ward.wid,
        ST_AsBinary(ST_Multi(sub.g))
      FROM sub
      JOIN ward
        ON ST_Intersects(sub.g, ward.wkb_geometry)
      WHERE sub.g IS NOT NULL
    $f$, id_expr, name_expr, quote_ident(wards_id_col));
  END IF;
END $$;

-- Indexes
DROP INDEX IF EXISTS idx_geo_wards_geom;
CREATE INDEX idx_geo_wards_geom ON geo_wards USING GIST (ST_GeomFromWKB(geom));
DROP INDEX IF EXISTS idx_geo_suburbs_geom;
CREATE INDEX idx_geo_suburbs_geom ON geo_suburbs USING GIST (ST_GeomFromWKB(geom));

