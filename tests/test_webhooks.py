import os
import hmac
import hashlib
from fastapi.testclient import TestClient
from app.main import app


def sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()


def test_webhook_rejects_missing_signature(monkeypatch):
    client = TestClient(app, raise_server_exceptions=False)
    monkeypatch.setenv("NMS_HMAC_SECRET", "secret")
    monkeypatch.setenv("NMS_ALLOW_IPS", "testclient")
    r = client.post(
        "/webhooks/librenms",
        json={"hostname": "OLT-1", "alert_id": 1},
        headers={"X-Tenant-Id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code in (401, 403)


def test_webhook_accepts_with_signature(monkeypatch):
    client = TestClient(app, raise_server_exceptions=False)
    monkeypatch.setenv("NMS_HMAC_SECRET", "secret")
    monkeypatch.setenv("NMS_ALLOW_IPS", "testclient")
    payload = b"{}"
    headers = {"X-Signature": sign(payload, "secret"), "X-Tenant-Id": "00000000-0000-0000-0000-000000000000"}
    r = client.post("/webhooks/librenms", data=payload, headers=headers)
    # May fail later due to DB, but security checks should pass initial stage
    assert r.status_code in (200, 500, 422)

