import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _h(role: str):
    return {"X-Role": role}


def test_docs_openapi():
    r = client.get("/openapi.json")
    assert r.status_code == 200


def test_assets_create_and_filters(monkeypatch):
    # Requires DB; skip if not configured
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")
    # create batch
    r = client.post("/assets", json={"type": "POLE", "sku": "P-7M", "count": 1}, headers=_h("ADMIN"))
    assert r.status_code == 200
    code = r.json()["codes"][0]
    # list
    r = client.get("/assets", headers=_h("ADMIN"))
    assert r.status_code == 200
    assert any(item["code"] == code for item in r.json()["items"])


def test_tasks_validation_roles():
    # Role required
    r = client.patch(f"/tasks/{uuid.uuid4()}", json={"status": "In Progress"})
    assert r.status_code == 403


def test_photos_upload_type_limit(monkeypatch):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")
    # upload wrong type
    files = {"file": ("test.txt", b"x" * 10, "text/plain")}
    r = client.post(f"/photos/upload?pon_id={uuid.uuid4()}", files=files, headers=_h("SITE"))
    assert r.status_code == 400
    assert r.json()["detail"] == "Unsupported file type"

