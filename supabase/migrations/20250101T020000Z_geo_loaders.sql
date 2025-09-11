-- Stats SA wards (2021) and SubPlaces (2011) loader
CREATE EXTENSION IF NOT EXISTS postgis;

-- Target tables
CREATE TABLE IF NOT EXISTS geo_wards (
  id   text PRIMARY KEY,
  name text NOT NULL,
  geom bytea NOT NULL
);

CREATE TABLE IF NOT EXISTS geo_suburbs (
  id      text PRIMARY KEY,
  name    text NOT NULL,
  ward_id text,
  geom    bytea NOT NULL
);

-- Ensure staging tables exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema='public' AND table_name='wards_src'
  ) THEN
    RAISE EXCEPTION 'Missing source table: wards_src';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema='public' AND table_name='suburbs_src'
  ) THEN
    RAISE EXCEPTION 'Missing source table: suburbs_src';
  END IF;
END $$;

-- Load wards (handle multiple field variants)
DO $$
DECLARE
  has_ward_id  boolean;
  has_ward_name boolean;
  has_code     boolean;
  has_name     boolean;
  has_wardno   boolean;
BEGIN
  TRUNCATE TABLE geo_wards;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='wards_src' AND column_name='ward_id'
  ) INTO has_ward_id;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='wards_src' AND column_name='ward_name'
  ) INTO has_ward_name;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='wards_src' AND column_name='code'
  ) INTO has_code;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='wards_src' AND column_name='name'
  ) INTO has_name;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='wards_src' AND column_name='wardno'
  ) INTO has_wardno;

  IF has_ward_id AND has_ward_name THEN
    EXECUTE $q$
      INSERT INTO geo_wards(id, name, geom)
      SELECT WARD_ID::text, WARD_NAME::text, ST_AsBinary(wkb_geometry)
      FROM wards_src
      WHERE wkb_geometry IS NOT NULL
    $q$;
  ELSIF has_code AND has_name THEN
    EXECUTE $q$
      INSERT INTO geo_wards(id, name, geom)
      SELECT CODE::text, NAME::text, ST_AsBinary(wkb_geometry)
      FROM wards_src
      WHERE wkb_geometry IS NOT NULL
    $q$;
  ELSIF has_wardno AND has_name THEN
    EXECUTE $q$
      INSERT INTO geo_wards(id, name, geom)
      SELECT WARDNO::text, NAME::text, ST_AsBinary(wkb_geometry)
      FROM wards_src
      WHERE wkb_geometry IS NOT NULL
    $q$;
  ELSE
    RAISE EXCEPTION 'Unable to determine ward id/name columns in wards_src. Expected one of: (WARD_ID, WARD_NAME) or (CODE, NAME) or (WARDNO, NAME).';
  END IF;
END $$;

-- Load suburbs; direct if WARD_ID present on suburbs, otherwise spatial join to wards
DO $$
DECLARE
  has_sp_code     boolean;
  has_sp_name     boolean;
  has_sub_code    boolean;
  has_sub_name    boolean;
  has_name        boolean;
  has_sub_ward_id boolean;
  ward_id_col     text;
  sub_id_expr     text;
  sub_name_expr   text;
BEGIN
  TRUNCATE TABLE geo_suburbs;

  -- suburb-side columns
  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='suburbs_src' AND column_name='sp_code'
  ) INTO has_sp_code;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='suburbs_src' AND column_name='sp_name'
  ) INTO has_sp_name;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='suburbs_src' AND column_name='sub_code'
  ) INTO has_sub_code;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='suburbs_src' AND column_name='sub_name'
  ) INTO has_sub_name;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='suburbs_src' AND column_name='name'
  ) INTO has_name;

  SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='suburbs_src' AND column_name='ward_id'
  ) INTO has_sub_ward_id;

  -- prefer existing ward_id on suburbs
  IF has_sub_ward_id THEN
    IF has_sp_code AND has_sp_name THEN
      EXECUTE $q$
        INSERT INTO geo_suburbs(id, name, ward_id, geom)
        SELECT SP_CODE::text, SP_NAME::text, WARD_ID::text, ST_AsBinary(wkb_geometry)
        FROM suburbs_src
        WHERE wkb_geometry IS NOT NULL
      $q$;
    ELSIF has_sub_code AND has_sub_name THEN
      EXECUTE $q$
        INSERT INTO geo_suburbs(id, name, ward_id, geom)
        SELECT SUB_CODE::text, SUB_NAME::text, WARD_ID::text, ST_AsBinary(wkb_geometry)
        FROM suburbs_src
        WHERE wkb_geometry IS NOT NULL
      $q$;
    ELSE
      -- fallback mapping using best-available id/name columns
      sub_id_expr := CASE
        WHEN has_sp_code THEN 'SP_CODE::text'
        WHEN has_sub_code THEN 'SUB_CODE::text'
        ELSE 'gid::text'
      END;

      sub_name_expr := CASE
        WHEN has_sp_name THEN 'SP_NAME::text'
        WHEN has_sub_name THEN 'SUB_NAME::text'
        WHEN has_name THEN 'NAME::text'
        ELSE 'gid::text'
      END;

      EXECUTE format($q$
        INSERT INTO geo_suburbs(id, name, ward_id, geom)
        SELECT %s, %s, WARD_ID::text, ST_AsBinary(wkb_geometry)
        FROM suburbs_src
        WHERE wkb_geometry IS NOT NULL
      $q$, sub_id_expr, sub_name_expr);
    END IF;

  ELSE
    -- Spatial join fallback: pick ward id column variant
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='wards_src' AND column_name='ward_id'
    ) THEN
      ward_id_col := 'WARD_ID';
    ELSIF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='wards_src' AND column_name='code'
    ) THEN
      ward_id_col := 'CODE';
    ELSIF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='wards_src' AND column_name='wardno'
    ) THEN
      ward_id_col := 'WARDNO';
    ELSE
      RAISE EXCEPTION 'Unable to determine ward id column in wards_src for spatial join.';
    END IF;

    sub_id_expr := CASE
      WHEN has_sp_code THEN 'SP_CODE::text'
      WHEN has_sub_code THEN 'SUB_CODE::text'
      ELSE 'gid::text'
    END;

    sub_name_expr := CASE
      WHEN has_sp_name THEN 'SP_NAME::text'
      WHEN has_sub_name THEN 'SUB_NAME::text'
      WHEN has_name THEN 'NAME::text'
      ELSE 'gid::text'
    END;

    EXECUTE format($q$
      WITH sub AS (
        SELECT
          gid,
          %s AS sid,
          %s AS sname,
          ST_Multi(ST_CollectionExtract(ST_MakeValid(wkb_geometry), 3)) AS g
        FROM suburbs_src
      ),
      ward AS (
        SELECT
          %I::text AS wid,
          ST_Multi(ST_CollectionExtract(ST_MakeValid(wkb_geometry), 3)) AS g
        FROM wards_src
      )
      INSERT INTO geo_suburbs(id, name, ward_id, geom)
      SELECT
        COALESCE(sub.sid, sub.gid::text),
        COALESCE(sub.sname, sub.gid::text),
        ward.wid,
        ST_AsBinary(sub.g)
      FROM sub
      JOIN ward
        ON ST_Intersects(sub.g, ward.g)
      WHERE sub.g IS NOT NULL
    $q$, sub_id_expr, sub_name_expr, ward_id_col);
  END IF;
END $$;

-- Spatial indexes on decoded geometries
DROP INDEX IF EXISTS idx_geo_wards_geom;
CREATE INDEX idx_geo_wards_geom ON geo_wards USING GIST (ST_GeomFromWKB(geom));

DROP INDEX IF EXISTS idx_geo_suburbs_geom;
CREATE INDEX idx_geo_suburbs_geom ON geo_suburbs USING GIST (ST_GeomFromWKB(geom));

