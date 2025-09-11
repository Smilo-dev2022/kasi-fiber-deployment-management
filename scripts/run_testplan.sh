#!/usr/bin/env bash
set -euo pipefail

API=${API:-http://localhost:8000}
ROLE=${ROLE:-ADMIN}
ORG_ID=${ORG_ID:-}
NMS_HMAC_SECRET=${NMS_HMAC_SECRET:-test}

hdrs=(-H "X-Role: $ROLE" -H "Content-Type: application/json")
if [[ -n "$ORG_ID" ]]; then
  hdrs+=(-H "X-Org-Id: $ORG_ID")
fi

require() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1" >&2; exit 2; }; }

require curl
require jq

echo "== Health =="
curl -fsS "$API/healthz" | cat
curl -fsS "$API/readyz" | cat || true

echo "== Create PON =="
PON_ID=$(curl -s -X POST "$API/pons" "${hdrs[@]}" -d '{"name":"PON-001","ward":"Ward 1"}' | jq -r '.id')
echo "PON_ID=$PON_ID"

echo "== Set geofence polygon =="
curl -fsS -X PATCH "$API/pons/$PON_ID/geofence" "${hdrs[@]}" \
  -d '{"type":"Polygon","coordinates":[[[24.0,-28.6],[24.01,-28.6],[24.01,-28.59],[24.0,-28.59],[24.0,-28.6]]]}' | cat

run_sql() {
  local sql="$1"
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f infra/docker-compose.yml exec -T db psql -U app -d app -Atc "$sql"
  elif command -v psql >/dev/null 2>&1 && [[ -n "${DATABASE_URL:-}" ]]; then
    psql "$DATABASE_URL" -Atc "$sql"
  else
    echo "No SQL execution path available (need docker compose or psql with DATABASE_URL)" >&2
    exit 3
  fi
}

echo "== Seed photo row =="
PHOTO_ID=$(run_sql "insert into photos (id, pon_id, taken_ts, gps_lat, gps_lng, exif_ok, within_geofence) values (gen_random_uuid(), '$PON_ID'::uuid, now(), -28.595, 24.005, true, true) returning id")
echo "PHOTO_ID=$PHOTO_ID"

echo "== Register geofence check =="
curl -fsS -X POST "$API/photos/register-geo" "${hdrs[@]}" -d '{"photo_id":"'"$PHOTO_ID"'"}' | cat

echo "== Create Test Plan =="
PLAN_ID=$(curl -s -X POST "$API/tests/plans" "${hdrs[@]}" -d '{"pon_id":"'"$PON_ID"'","link_name":"Feeder A","from_point":"OLT","to_point":"SPL01","wavelength_nm":1310,"max_loss_db":0.35}' | jq -r '.id')
echo "PLAN_ID=$PLAN_ID"

echo "== OTDR fail then pass =="
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/tests/otdr" "${hdrs[@]}" -d '{"test_plan_id":"'"$PLAN_ID"'","file_url":"s3://bucket/otdr1.sor","total_loss_db":0.6,"passed":false}' | grep -E "^(2|4)" || true
curl -fsS -X POST "$API/tests/otdr" "${hdrs[@]}" -d '{"test_plan_id":"'"$PLAN_ID"'","file_url":"s3://bucket/otdr2.sor","total_loss_db":0.1,"passed":true}' | cat

echo "== LSPM fail then pass =="
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/tests/lspm" "${hdrs[@]}" -d '{"test_plan_id":"'"$PLAN_ID"'","wavelength_nm":1310,"measured_loss_db":0.9,"passed":false}' | grep -E "^(2|4)" || true
curl -fsS -X POST "$API/tests/lspm" "${hdrs[@]}" -d '{"test_plan_id":"'"$PLAN_ID"'","wavelength_nm":1310,"measured_loss_db":0.2,"passed":true}' | cat

echo "== LibreNMS webhook sample =="
BODY='{"hostname":"OLT-01","severity":"critical","rule":"Device Down","alert_id":12345,"state":"alert","msg":"OLT-01 no response"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$NMS_HMAC_SECRET" -binary | xxd -p -c 256)
curl -fsS -X POST "$API/webhooks/librenms" -H "Content-Type: application/json" -H "X-Signature: $SIG" --data-binary "$BODY" | cat

echo "== List incidents =="
curl -fsS "$API/incidents" "${hdrs[@]}" | jq 'length'

echo "== Maps =="
curl -fsS "$API/map/wards" "${hdrs[@]}" | jq '.features | length'
curl -fsS "$API/map/pon/$PON_ID/assets" "${hdrs[@]}" | jq '.features | length'

echo "Done"

