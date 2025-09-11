#!/usr/bin/env bash
set -euo pipefail

# Import Stats SA Wards (2021) and SubPlace (2011) shapefiles
# into staging tables (wards_src, suburbs_src) and run loader SQL

# Usage:
#   ./scripts/import_sa_geographies.sh \
#     --pg "postgresql://user:pass@localhost:5432/dbname" \
#     --wards /path/to/wards.shp \
#     --suburbs /path/to/suburbs.shp

PG_DSN=""
WARDS_SHP=""
SUBURBS_SHP=""
SCHEMA="public"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pg)
      PG_DSN="$2"; shift 2 ;;
    --wards)
      WARDS_SHP="$2"; shift 2 ;;
    --suburbs)
      SUBURBS_SHP="$2"; shift 2 ;;
    --schema)
      SCHEMA="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,30p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$PG_DSN" || -z "$WARDS_SHP" || -z "$SUBURBS_SHP" ]]; then
  echo "Missing required args. See --help" >&2
  exit 1
fi

echo "Creating/clearing staging tables..."
psql "$PG_DSN" -v ON_ERROR_STOP=1 -c "
  CREATE EXTENSION IF NOT EXISTS postgis;
  DROP TABLE IF EXISTS ${SCHEMA}.wards_src;
  DROP TABLE IF EXISTS ${SCHEMA}.suburbs_src;
  -- Create empty tables with geometry type inferred via ogr2ogr
  CREATE TABLE ${SCHEMA}.wards_src (dummy int);
  DROP TABLE ${SCHEMA}.wards_src;
  CREATE TABLE ${SCHEMA}.suburbs_src (dummy int);
  DROP TABLE ${SCHEMA}.suburbs_src;
"

echo "Importing wards shapefile: $WARDS_SHP"
ogr2ogr -f PostgreSQL \
  PG:"$PG_DSN" \
  "$WARDS_SHP" \
  -nln "${SCHEMA}.wards_src" \
  -lco GEOMETRY_NAME=wkb_geometry \
  -lco FID=gid \
  -nlt PROMOTE_TO_MULTI \
  -skipfailures \
  -overwrite

echo "Importing suburbs shapefile: $SUBURBS_SHP"
ogr2ogr -f PostgreSQL \
  PG:"$PG_DSN" \
  "$SUBURBS_SHP" \
  -nln "${SCHEMA}.suburbs_src" \
  -lco GEOMETRY_NAME=wkb_geometry \
  -lco FID=gid \
  -nlt PROMOTE_TO_MULTI \
  -skipfailures \
  -overwrite

echo "Running loader SQL..."
psql "$PG_DSN" -v ON_ERROR_STOP=1 -f "/workspace/sql/load_sa_geographies.sql"

echo "Done. Counts:"
psql "$PG_DSN" -v ON_ERROR_STOP=1 -c "
  SELECT 'geo_wards' AS table, COUNT(*) FROM ${SCHEMA}.geo_wards
  UNION ALL
  SELECT 'geo_suburbs' AS table, COUNT(*) FROM ${SCHEMA}.geo_suburbs;
"

