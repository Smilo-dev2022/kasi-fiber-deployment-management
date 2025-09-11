# Webhook Security

- Require HMAC signatures and IP allowlisting
- Reject unsigned or unknown IP traffic
- Rotate secrets and monitor failures via alerts

## FastAPI Example (HMAC)
```python
import hmac, hashlib
from fastapi import Header, HTTPException
from starlette.requests import Request

NMS_HMAC_SECRET = os.getenv("NMS_HMAC_SECRET", "")

async def verify_signature(request: Request, x_signature: str = Header(None)):
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    body = await request.body()
    digest = hmac.new(NMS_HMAC_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

## IP Allowlist
- Set `NMS_ALLOW_IPS` with comma-separated IPs for webhook sources
- Middleware or router dependencies should enforce allowlist (see `app/core/limiter.py`)

## Postman and cURL
- Provide a Postman collection and example `curl` calls for each webhook
- Include sample payloads, headers (`X-Signature`), and expected responses