# API Test Plan (curl)

Export an auth header first. For local dev without JWT, pass `X-Role` and `X-Org-Id` headers instead of `Authorization`.

```bash
export API="http://localhost:8000"
export AUTH_HEADER="-H X-Role: ADMIN"
# If you know an org UUID for scoping-sensitive endpoints:
# export ORG_HEADER="-H X-Org-Id: YOUR_ORG_UUID"
```

## Health

```bash
curl -s "$API/healthz"
curl -s "$API/readyz"
```

## PON and geofence

Create PON:
```bash
PON_ID=$(curl -s -X POST "$API/pons" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" -d '{"name":"PON-001","ward":"Ward 1"}' | jq -r '.id')
echo "$PON_ID"
```

Set geofence polygon:
```bash
curl -s -X PATCH "$API/pons/$PON_ID/geofence" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"type":"Polygon","coordinates":[[[24.0,-28.6],[24.01,-28.6],[24.01,-28.59],[24.0,-28.59],[24.0,-28.6]]]}'
```

## Photo evidence gate

Register a placeholder photo record then validate EXIF/geofence via S3 stub (skip if unavailable):
```bash
# Create a photo row linked to the PON
PHOTO_ID=$(psql "$DATABASE_URL" -Atc "insert into photos (id, pon_id) values (gen_random_uuid(), '$PON_ID'::uuid) returning id")
echo "$PHOTO_ID"

# If S3 integration is configured, register upload (expects s3_key metadata)
# curl -s -X POST "$API/photos/register" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
#   -d '{"photo_id":"'$PHOTO_ID'","s3_key":"tmp/demo.jpg"}'

# Alternatively mark within geofence using existing lat/lng on photo and polygon via register-geo
curl -s -X POST "$API/photos/register-geo" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"photo_id":"'$PHOTO_ID'"}'

# Validate EXIF + center/radius flow (requires PON center configured)
# curl -s -X POST "$API/photos/validate" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
#   -d '{"photo_id":"'$PHOTO_ID'"}'
```

## Certificate of Acceptance

Expect failure without validated photo, then success after you ensure a valid photo exists.
```bash
curl -i -X POST "$API/certificate-acceptance" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"pon_id":"'$PON_ID'","pole_length_m":7.6,"depth_m":1.2,"tag_height_m":2.25}' | grep -E "^(HTTP|HTTP/|400|403|409)" || true

# After seeding valid photo evidence, expect 200
# curl -s -X POST "$API/certificate-acceptance" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
#  -d '{"pon_id":"'$PON_ID'","pole_length_m":7.6,"depth_m":1.2,"tag_height_m":2.25}'
```

## Technical gates: Test Plans, OTDR, LSPM

Create Test Plan:
```bash
PLAN_ID=$(curl -s -X POST "$API/tests/plans" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"pon_id":"'$PON_ID'","link_name":"Feeder A","from_point":"OLT","to_point":"SPL01","wavelength_nm":1310,"max_loss_db":0.35}' | jq -r '.id')
echo "$PLAN_ID"
```

OTDR add (fail vs pass controlled by payload.passed):
```bash
curl -i -X POST "$API/tests/otdr" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"test_plan_id":"'$PLAN_ID'","file_url":"s3://bucket/otdr1.sor","total_loss_db":0.6,"passed":false}' | grep "HTTP/1.1" || true

curl -s -X POST "$API/tests/otdr" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"test_plan_id":"'$PLAN_ID'","file_url":"s3://bucket/otdr2.sor","total_loss_db":0.1,"passed":true}'
```

LSPM add (fail vs pass controlled by payload.passed):
```bash
curl -i -X POST "$API/tests/lspm" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"test_plan_id":"'$PLAN_ID'","wavelength_nm":1310,"measured_loss_db":0.9,"passed":false}' | grep "HTTP/1.1" || true

curl -s -X POST "$API/tests/lspm" $AUTH_HEADER ${ORG_HEADER:-} -H "Content-Type: application/json" \
  -d '{"test_plan_id":"'$PLAN_ID'","wavelength_nm":1310,"measured_loss_db":0.2,"passed":true}'
```

## Incidents and SLAs

LibreNMS webhook (HMAC):
```bash
SECRET=${NMS_HMAC_SECRET:-test}
BODY=$(cat <<'JSON'
{"hostname":"OLT-01","severity":"critical","rule":"Device Down","alert_id":12345,"state":"alert","msg":"OLT-01 no response"}
JSON
)
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -binary | xxd -p -c 256)
curl -s -X POST "$API/webhooks/librenms" -H "Content-Type: application/json" -H "X-Signature: $SIG" --data-binary "$BODY"
```

List incidents:
```bash
curl -s "$API/incidents" $AUTH_HEADER ${ORG_HEADER:-}
```

## Stock

Issue/return via spares API (requires seeded store and stock):
```bash
# Example only; adjust UUIDs as per seed output
# curl -s -X POST "$API/spares/issue" $AUTH_HEADER -H "Content-Type: application/json" \
#   -d '{"store_id":"STORE_UUID","sku":"FIBER-24C","qty":1,"incident_id":null}'
```

## Finance

Pay sheet generate and export:
```bash
# Replace SMME_ID from seed output
# PS_ID=$(curl -s -X POST "$API/pay-sheets/generate" $AUTH_HEADER -H "Content-Type: application/json" \
#   -d '{"smme_id":"SMME_UUID","period_start":"2025-01-01","period_end":"2025-01-31"}' | jq -r '.pay_sheet_id')
# curl -s "$API/pay-sheets/$PS_ID/pdf" $AUTH_HEADER
```

## Maps

Wards and PON assets:
```bash
curl -s "$API/map/wards" $AUTH_HEADER | jq '.features | length'
curl -s "$API/map/pon/$PON_ID/assets" $AUTH_HEADER | jq '.features | length'
```

## Health quick-check script

```bash
./scripts/smoke.sh
```

