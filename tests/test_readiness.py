import os
from fastapi.testclient import TestClient

from app.main import app


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ops_readiness_endpoint():
    os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://example.com")
    client = TestClient(app)
    r = client.get("/ops/readiness")
    assert r.status_code == 200
    data = r.json()
    assert "checks" in data

