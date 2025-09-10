import hmac
import os
import time
from hashlib import sha256
from typing import Dict

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.incident import Incident
from app.models.device import Device


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


_RATE_BUCKET: Dict[str, list[float]] = {}


def _rate_limited(ip: str, limit: int = 60, window_seconds: int = 60) -> bool:
    now = time.time()
    bucket = _RATE_BUCKET.setdefault(ip, [])
    # prune old
    cutoff = now - window_seconds
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def _check_ip_whitelist(request: Request) -> None:
    whitelist = os.getenv("NMS_WEBHOOK_IP_WHITELIST", "").strip()
    if not whitelist:
        return
    allowed = {ip.strip() for ip in whitelist.split(",") if ip.strip()}
    client_ip = request.client.host if request.client else ""
    if client_ip not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden: IP not allowed")


def _check_hmac(request: Request, body_bytes: bytes) -> None:
    secret = os.getenv("NMS_WEBHOOK_HMAC_SECRET", "")
    header_name = os.getenv("NMS_WEBHOOK_HMAC_HEADER", "X-Signature")
    if not secret:
        return
    provided = request.headers.get(header_name)
    if not provided:
        raise HTTPException(status_code=401, detail="Missing signature")
    computed = hmac.new(secret.encode(), body_bytes, sha256).hexdigest()
    if not hmac.compare_digest(provided, computed):
        raise HTTPException(status_code=401, detail="Invalid signature")


# LibreNMS configured alert transport
# Example JSON fields used: hostname, state, severity, rule, alert_id, timestamp, msg
@router.post("/librenms")
async def librenms(request: Request, db: Session = Depends(get_db)):
    _check_ip_whitelist(request)
    if _rate_limited(request.client.host if request.client else ""):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    raw = await request.body()
    _check_hmac(request, raw)
    data = await request.json()
    host = data.get("hostname")
    sev = data.get("severity", "critical").lower()
    rule = data.get("rule", "LibreNMS Alert")
    alert_id = str(data.get("alert_id"))
    msg = data.get("msg", "")
    state = data.get("state", "alert")

    device = db.query(Device).filter(Device.name == host).first()
    severity_map = {"critical": "P1", "major": "P2", "minor": "P3", "warning": "P3", "info": "P4"}
    category = "Device"
    title = f"{host} {rule} {state}"

    inc = Incident(
        device_id=device.id if device else None,
        pon_id=device.pon_id if device else None,
        severity=severity_map.get(sev, "P3"),
        category=category,
        title=title,
        description=msg,
        status="Open",
        nms_ref=f"librenms:{alert_id}",
        opened_at=datetime.now(timezone.utc),
    )
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}


# Zabbix webhook
# Expect { "host": "OLT-01", "severity": "Disaster|High|Average|Warning|Info", "event_id": "123", "problem": true, "name": "Link down", "message": "..." }
@router.post("/zabbix")
async def zabbix(request: Request, db: Session = Depends(get_db)):
    _check_ip_whitelist(request)
    if _rate_limited(request.client.host if request.client else ""):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    raw = await request.body()
    _check_hmac(request, raw)
    data = await request.json()
    host = data.get("host")
    sev = str(data.get("severity", "Average"))
    problem = bool(data.get("problem", True))
    name = data.get("name", "Zabbix Alert")
    event_id = str(data.get("event_id", ""))
    msg = data.get("message", "")

    device = db.query(Device).filter(Device.name == host).first()
    severity_map = {"Disaster": "P1", "High": "P2", "Average": "P3", "Warning": "P3", "Info": "P4"}
    status = "Open" if problem else "Resolved"

    inc = Incident(
        device_id=device.id if device else None,
        pon_id=device.pon_id if device else None,
        severity=severity_map.get(sev, "P3"),
        category="Device",
        title=f"{host} {name}",
        description=msg,
        status=status,
        nms_ref=f"zabbix:{event_id}",
        opened_at=datetime.now(timezone.utc),
        resolved_at=None if problem else datetime.now(timezone.utc),
    )
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}

