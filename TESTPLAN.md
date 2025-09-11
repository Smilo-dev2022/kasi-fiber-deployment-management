## API Test Plan

Set variables:

```bash
export API="http://localhost:8000"
export AUTH="Authorization: Bearer YOUR_JWT"
```

### Health

```bash
curl -s $API/healthz | cat
curl -s $API/readyz | cat
```

### PON and Geofence

Create Test Plan requires an existing PON ID. Use seed output to capture one.

Set polygon geofence:
```bash
curl -s -X POST $API/pons/PON_ID/geofence/polygon \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"geometry":{"type":"Polygon","coordinates":[[[24.0,-28.6],[24.01,-28.6],[24.01,-28.59],[24.0,-28.59],[24.0,-28.6]]]}}' | cat
```

### Photo evidence gate

Register S3 photo and validate:
```bash
# Create photo row externally, then register S3 object for EXIF
curl -s -X POST $API/photos/register \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"photo_id":"PHOTO_ID","s3_key":"photos/PHOTO_KEY.jpg"}' | cat

# Validate against geofence
curl -s -X POST $API/photos/register-geo \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"photo_id":"PHOTO_ID"}' | cat
```

Attempt to complete task without required evidence (should 400):
```bash
curl -i -X PATCH $API/tasks/TASK_ID \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"status":"Done"}' | grep -E "400|Forbidden|Bad Request" || true
```

### Certificate of Acceptance

Pass:
```bash
curl -s -X POST $API/certificate-acceptance \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"pon_id":"PON_ID","depth_m":1.2,"tag_height_m":2.25,"pole_length_m":7.6}' | cat
```

Fail (validation error 400):
```bash
curl -i -X POST $API/certificate-acceptance \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"pon_id":"PON_ID","depth_m":0.9,"tag_height_m":1.8,"pole_length_m":6.8}' | grep "400" || true
```

### Stringing

Add run (placeholder via tasks):
```bash
curl -s -X PATCH $API/tasks/TASK_ID \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"status":"In Progress"}' | cat
```

### Technical gates

Create Test Plan:
```bash
curl -s -X POST $API/tests/plans \
 -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"pon_id":"PON_ID","link_name":"L1","from_point":"OLT","to_point":"ONU","wavelength_nm":1550,"max_loss_db":0.35,"otdr_required":true,"lspm_required":true}' | cat
```

Add OTDR (fail then pass):
```bash
TP=TEST_PLAN_ID
curl -i -X POST $API/tests/otdr -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"test_plan_id":"'$TP'","file_url":"s3://bucket/otdr.sor","wavelength_nm":1550,"total_loss_db":1.2,"max_splice_loss_db":0.6,"passed":false}' | grep "200\|400" || true
curl -s -X POST $API/tests/otdr -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"test_plan_id":"'$TP'","file_url":"s3://bucket/otdr.sor","wavelength_nm":1550,"total_loss_db":0.1,"max_splice_loss_db":0.1,"passed":true}' | cat
```

Add LSPM (fail then pass):
```bash
curl -i -X POST $API/tests/lspm -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"test_plan_id":"'$TP'","wavelength_nm":1550,"measured_loss_db":0.9,"margin_db":-0.1,"passed":false}' | grep "200\|400" || true
curl -s -X POST $API/tests/lspm -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"test_plan_id":"'$TP'","wavelength_nm":1550,"measured_loss_db":0.2,"margin_db":0.1,"passed":true}' | cat
```

### Incidents & SLAs (webhooks)

HMAC signature:
```bash
SIG=$(echo -n '{"hostname":"OLT-01","severity":"critical","rule":"Device Down","alert_id":12345,"state":"alert","msg":"OLT-01 no response"}' \
 | openssl dgst -sha256 -hmac "$NMS_HMAC" -binary | xxd -p -c 256)
curl -s -X POST $API/webhooks/librenms -H "X-Signature: $SIG" -H "Content-Type: application/json" \
 --data-binary @docs/samples/librenms.json | cat
```

List incidents:
```bash
curl -s $API/incidents -H "$AUTH" | cat
```

### Stock

Receive batch:
```bash
curl -s -X POST $API/spares/issue -H "$AUTH" -H "Content-Type: application/json" \
 -d '{"pon_id":"PON_ID","asset_code":"FIBER-24C"}' | cat
```

### Finance

Pay sheet
```bash
curl -s "$API/pay-sheets?smme_id=SMME_ID&from=2025-01-01&to=2025-01-31" -H "$AUTH" | cat
```

Invoice PDF (generate):
```bash
curl -s -X POST $API/invoices -H "$AUTH" -H "Content-Type: application/json" -d '{"pon_id":"PON_ID"}' -o invoice.pdf
```

### Maps

Wards:
```bash
curl -s $API/map/wards -H "$AUTH" | jq '.features | length'
```

PON assets:
```bash
curl -s $API/map/pon/PON_ID/assets -H "$AUTH" | jq '.features | length'
```

## Local Authentication for Testing

When running locally with Docker Compose:

1. Start services:

```bash
make up
```

2. Seed a test user for the Node auth service:

```bash
make seed-user
```

3. Use the following endpoints via the client (proxying to `/api/*`) or directly to `http://localhost:5000/api`:

- POST `/auth/register`
- POST `/auth/login`
- GET `/auth/user`

4. The Node auth container proxies map and health routes to the FastAPI container to keep the client working end-to-end.

