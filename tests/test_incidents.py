import os
import jwt
from fastapi.testclient import TestClient
from app.main import app


def make_token(tenant_id: str, roles: list[str]):
    secret = os.environ.get("JWT_SECRET", "test")
    return jwt.encode({"tenant_id": tenant_id, "roles": roles}, secret, algorithm=os.environ.get("JWT_ALGORITHM", "HS256"))


def test_list_incidents_scoped(monkeypatch):
    client = TestClient(app)
    token = make_token("11111111-1111-1111-1111-111111111111", ["PM"])  # uuid format
    res = client.get("/incidents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in (200, 204)

