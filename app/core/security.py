import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException, Request

from app.core.settings import get_settings


def compute_hmac_sha256(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def verify_webhook_hmac(request: Request, body: bytes) -> bool:
    settings = get_settings()
    provided: Optional[str] = (
        request.headers.get("X-Hub-Signature-256")
        or request.headers.get("X-LibreNMS-Signature")
        or request.headers.get("X-Zabbix-Signature")
        or request.headers.get("X-Signature")
    )
    if not provided:
        return False
    value = provided
    if value.startswith("sha256="):
        value = value.split("=", 1)[1]
    calc = compute_hmac_sha256(settings.NMS_HMAC_SECRET, body)
    return constant_time_equals(value, calc)


def get_client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""


def enforce_ip_whitelist(request: Request):
    settings = get_settings()
    ip = get_client_ip(request)
    if settings.ip_allowlist and ip not in settings.ip_allowlist:
        raise HTTPException(status_code=403, detail="Forbidden IP")

