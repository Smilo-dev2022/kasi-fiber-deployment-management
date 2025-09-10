import hmac
import hashlib
import os
from datetime import datetime, timezone, timedelta
from collections import deque
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from app.core.deps import get_scoped_db
from app.models.maint import MaintWindow
from app.models.incident import Incident
from app.models.device import Device


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# LibreNMS configured alert transport
# Example JSON fields used: hostname, state, severity, rule, alert_id, timestamp, msg
def _verify_source(request: Request):
    allow_ips = os.getenv("NMS_ALLOW_IPS", "").split(",")
    allow_ips = [ip.strip() for ip in allow_ips if ip.strip()]
    if allow_ips:
        ip = request.client.host if request.client else None
        if ip not in allow_ips:
            raise HTTPException(403, "IP not allowed")


def _verify_hmac(request: Request, body: bytes):
    secret = os.getenv("NMS_HMAC_SECRET")
    if not secret:
        return
    sig = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature")
    if not sig:
        raise HTTPException(401, "Missing signature")
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, mac):
        raise HTTPException(401, "Invalid signature")


_RATE_BUCKETS: dict[str, deque] = {}


def _rate_limit(request: Request, limit_per_minute: int = 60):
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}:{request.url.path}"
    q = _RATE_BUCKETS.setdefault(key, deque())
    now_ts = datetime.now(timezone.utc).timestamp()
    while q and now_ts - q[0] > 60:
        q.popleft()
    if len(q) >= limit_per_minute:
        raise HTTPException(429, "Rate limit exceeded")
    q.append(now_ts)


def _dedup_recent(db: Session, nms_ref: str, category: str, device_id):
    # Get dedupe window per device/category, fallback 30min
    window_min = 30
    if device_id:
        try:
            row = db.execute(
                text("select window_min from alert_dedupe where device_id = :d and category = :c"),
                {"d": str(device_id), "c": category},
            ).first()
            if row and row[0]:
                window_min = int(row[0])
        except Exception:
            # table may not exist yet
            pass
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_min)
    existing = (
        db.query(Incident)
        .filter(and_(Incident.nms_ref == nms_ref, Incident.category == category, Incident.opened_at >= cutoff))
        .first()
    )
    return existing


def _suppressed(db: Session, device: Device | None, pon_id):
    now = datetime.now(timezone.utc)
    # Global or org/pon scoped windows
    q = db.query(MaintWindow).filter(MaintWindow.start_at <= now).filter(MaintWindow.end_at >= now)
    # Scope matching: device, pon, global
    if device:
        dev_match = q.filter(MaintWindow.scope == "device").filter(MaintWindow.target_id == device.id).first()
        if dev_match:
            return True
    if pon_id:
        pon_match = q.filter(MaintWindow.scope == "pon").filter(MaintWindow.target_id == pon_id).first()
        if pon_match:
            return True
    glob = q.filter(MaintWindow.scope == "global").first()
    return bool(glob)


@router.post("/librenms")
async def librenms(request: Request, db: Session = Depends(get_scoped_db)):
    _rate_limit(request)
    _verify_source(request)
    raw = await request.body()
    _verify_hmac(request, raw)
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

    nms_ref = f"librenms:{alert_id}"
    if _suppressed(db, device, device.pon_id if device else None):
        return {"ok": True, "suppressed": True}
    existing = _dedup_recent(db, nms_ref, category, device.id if device else None)
    if existing:
        return {"ok": True, "incident_id": str(existing.id), "dedup": True}

    inc = Incident(
        device_id=device.id if device else None,
        pon_id=device.pon_id if device else None,
        severity=severity_map.get(sev, "P3"),
        category=category,
        title=title,
        description=msg,
        status="Open",
        nms_ref=nms_ref,
        opened_at=datetime.now(timezone.utc),
    )
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}


# Zabbix webhook
# Expect { "host": "OLT-01", "severity": "Disaster|High|Average|Warning|Info", "event_id": "123", "problem": true, "name": "Link down", "message": "..." }
@router.post("/zabbix")
async def zabbix(request: Request, db: Session = Depends(get_scoped_db)):
    _rate_limit(request)
    _verify_source(request)
    raw = await request.body()
    _verify_hmac(request, raw)
    data = await request.json()
    host = data.get("host")
    sev = str(data.get("severity", "Average"))
    problem = bool(data.get("problem", True))
    name = data.get("name", "Zabbix Alert")
    event_id = str(data.get("event_id", ""))
    msg = data.get("message", "")

    device = db.query(Device).filter(Device.name == host).first()
    severity_map = {"Disaster": "P1", "High": "P2", "Average": "P3", "Warning": "P3", "Info": "P4"}
    nms_ref = f"zabbix:{event_id}"
    if problem:
        if _suppressed(db, device, device.pon_id if device else None):
            return {"ok": True, "suppressed": True}
        existing = _dedup_recent(db, nms_ref, "Device", device.id if device else None)
        if existing:
            return {"ok": True, "incident_id": str(existing.id), "dedup": True}
        inc = Incident(
            device_id=device.id if device else None,
            pon_id=device.pon_id if device else None,
            severity=severity_map.get(sev, "P3"),
            category="Device",
            title=f"{host} {name}",
            description=msg,
            status="Open",
            nms_ref=nms_ref,
            opened_at=datetime.now(timezone.utc),
        )
        db.add(inc)
        db.commit()
        return {"ok": True, "incident_id": str(inc.id)}
    else:
        # Clear handler: mark existing as resolved
        inc = (
            db.query(Incident)
            .filter(Incident.nms_ref == nms_ref)
            .filter(Incident.status != "Closed")
            .order_by(Incident.opened_at.desc())
            .first()
        )
        if inc:
            inc.status = "Resolved"
            inc.resolved_at = datetime.now(timezone.utc)
            db.commit()
            return {"ok": True, "incident_id": str(inc.id), "cleared": True}
        return {"ok": True, "message": "No open incident"}

