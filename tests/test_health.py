import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENV", "development")

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True

