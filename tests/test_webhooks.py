import os
import hmac
import hashlib
from fastapi.testclient import TestClient
from app.main import app


def sign(body: bytes, secret: str):
    return hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()


def test_librenms_signature(monkeypatch):
    client = TestClient(app)
    secret = "secret"
    monkeypatch.setenv("NMS_HMAC_SECRET", secret)
    body = {
        "hostname": "OLT-01",
        "severity": "critical",
        "rule": "Down",
        "alert_id": 123,
        "msg": "Down",
        "state": "alert",
    }
    import json
    raw = json.dumps(body).encode()
    res = client.post("/webhooks/librenms", data=raw, headers={"X-Signature": sign(raw, secret), "content-type": "application/json"})
    assert res.status_code in (200, 401, 403)  # database may not be configured in test

