#!/usr/bin/env bash
set -euo pipefail

log() { printf "[%s] %s\n" "$(date +'%Y-%m-%dT%H:%M:%S')" "$*"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' not found in PATH" >&2
    exit 1
  fi
}

# Ensure required tools are available
require_cmd psql
require_cmd ogr2ogr

DATABASE_URL="${DATABASE_URL:-}"
if [ -z "$DATABASE_URL" ]; then
  echo "Error: DATABASE_URL is not set. Example: export DATABASE_URL=\"postgresql://app:app@localhost:5432/app\"" >&2
  exit 1
fi

# Optional overrides from environment
WARDS_SHP="${WARDS_SHP:-/workspace/data/za_wards/wards.shp}"
SUBURBS_SHP="${SUBURBS_SHP:-/workspace/data/za_suburbs/suburbs.shp}"

wait_for_db() {
  local max_tries=30
  local i
  for i in $(seq 1 "$max_tries"); do
    if psql "$DATABASE_URL" -tAc 'select 1' >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

log "Waiting for database availability..."
if ! wait_for_db; then
  echo "Error: could not connect to database at DATABASE_URL after waiting." >&2
  exit 1
fi

log "Ensuring PostGIS extension exists (no-op if already installed)"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS postgis;" | cat

log "Ensuring optional schema tables exist (geo_wards, geo_suburbs)"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "/workspace/sql/schema_optional.sql" | cat

run_ogr() {
  local shp="$1"
  local layer_name="$2"
  if [ -f "$shp" ]; then
    log "Loading $shp into table $layer_name via ogr2ogr (EPSG:4326)"
    ogr2ogr -f "PostgreSQL" \
      PG:"$DATABASE_URL" "$shp" \
      -nln "$layer_name" \
      -t_srs EPSG:4326 \
      -nlt PROMOTE_TO_MULTI \
      -lco GEOMETRY_NAME=geom \
      -overwrite | cat
  else
    log "Skipping $layer_name load: shapefile not found at $shp"
  fi
}

run_ogr "$WARDS_SHP" "wards_src"
run_ogr "$SUBURBS_SHP" "suburbs_src"

# Only run geo load mapping if staging tables exist
have_wards_src=$(psql "$DATABASE_URL" -Atc "select coalesce(to_regclass('public.wards_src')::text,'')")
have_suburbs_src=$(psql "$DATABASE_URL" -Atc "select coalesce(to_regclass('public.suburbs_src')::text,'')")

if [ -n "$have_wards_src" ] || [ -n "$have_suburbs_src" ]; then
  log "Populating geo_wards and geo_suburbs from staging"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "/workspace/sql/geo_load.sql" | cat
else
  log "Skipping geo table population: no staging tables present"
fi

log "Running backfill of geometry JSON and PON geofences (safe, conditional)"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "/workspace/sql/backfill_geoms.sql" | cat
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "/workspace/sql/pons_geofence.sql" | cat

log "Running sanity checks"
psql "$DATABASE_URL" -v ON_ERROR_STOP=0 -f "/workspace/sql/sanity_checks.sql" | cat

log "Done"

