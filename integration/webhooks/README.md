# Webhooks

All webhook deliveries are HMAC-SHA256 signed.

- Header: `X-Signature: <hex digest>`
- Body: raw request body is signed with your shared secret.
- Reject requests not from allowlisted IPs and any with missing/invalid signature.

## Verification example (bash)

```bash
payload='{"event":"ping"}'
secret="REPLACE_ME"
printf %s "$payload" | openssl dgst -sha256 -hmac "$secret" | awk '{print $2}'
```

## Example curl delivery

```bash
curl -X POST "https://your-endpoint.example.com/webhooks/ingest" \
  -H "X-Signature: $(printf %s '{"event":"ping"}' | openssl dgst -sha256 -hmac "$WEBHOOK_HMAC_SECRET" | awk '{print $2}')" \
  -H "Content-Type: application/json" \
  -d '{"event":"ping"}'
```