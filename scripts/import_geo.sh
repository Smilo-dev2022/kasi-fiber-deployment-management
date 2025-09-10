#!/usr/bin/env bash
set -euo pipefail

# Import Stats SA wards and suburbs shapefiles into PostGIS and run loader SQL

# Required env vars:
#   - PGHOST, PGPORT (default 5432), PGUSER, PGPASSWORD (optional if using .pgpass), PGDATABASE
#   - WARDS_SHP: path to Wards 2021 shapefile (.shp) or datasource
#   - SUBURBS_SHP: path to SubPlace 2011 shapefile (.shp) or datasource
# Optional:
#   - WARDS_LAYER (default: wards)
#   - SUBURBS_LAYER (default: suburbs)

if ! command -v ogr2ogr >/dev/null 2>&1; then
  echo "ogr2ogr is required (GDAL). Please install GDAL." >&2
  exit 1
fi
if ! command -v ogrinfo >/dev/null 2>&1; then
  echo "ogrinfo is required (GDAL). Please install GDAL." >&2
  exit 1
fi
if ! command -v psql >/dev/null 2>&1; then
  echo "psql is required. Please install PostgreSQL client tools." >&2
  exit 1
fi

PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
PGUSER=${PGUSER:-$(whoami)}
PGDATABASE=${PGDATABASE:-postgres}
PGPASSWORD=${PGPASSWORD:-}

if [[ -z "${WARDS_SHP:-}" || -z "${SUBURBS_SHP:-}" ]]; then
  echo "Please set WARDS_SHP and SUBURBS_SHP environment variables to the input datasets." >&2
  exit 1
fi

WARDS_LAYER=${WARDS_LAYER:-wards}
SUBURBS_LAYER=${SUBURBS_LAYER:-suburbs}

echo "Inspecting layers..."
set +e
ogrinfo -so "$WARDS_SHP" "$WARDS_LAYER" | cat
ogrinfo -so "$SUBURBS_SHP" "$SUBURBS_LAYER" | cat
set -e

PG_CONNSTR="PG:host=${PGHOST} port=${PGPORT} user=${PGUSER} dbname=${PGDATABASE}${PGPASSWORD:+ password=${PGPASSWORD}}"

echo "Ensuring PostGIS extension exists..."
psql -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS postgis;" >/dev/null

echo "Importing wards into table wards_src..."
ogr2ogr \
  -f PostgreSQL "$PG_CONNSTR" "$WARDS_SHP" \
  -nln wards_src \
  -lco GEOMETRY_NAME=wkb_geometry \
  -lco FID=gid \
  -nlt PROMOTE_TO_MULTI \
  -overwrite

echo "Importing suburbs into table suburbs_src..."
ogr2ogr \
  -f PostgreSQL "$PG_CONNSTR" "$SUBURBS_SHP" \
  -nln suburbs_src \
  -lco GEOMETRY_NAME=wkb_geometry \
  -lco FID=gid \
  -nlt PROMOTE_TO_MULTI \
  -overwrite

echo "Running SQL loader..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
psql -v ON_ERROR_STOP=1 -f "$ROOT_DIR/sql/load_geo.sql"

echo "Done. Tables populated: geo_wards, geo_suburbs."

