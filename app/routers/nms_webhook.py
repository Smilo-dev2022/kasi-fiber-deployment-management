import hmac
import hashlib
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.deps import get_db
from app.models.incident import Incident
from app.models.device import Device
from app.core.limits import limiter


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


def _dedup_recent(db: Session, nms_ref: str, category: str, device_id):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    existing = (
        db.query(Incident)
        .filter(and_(Incident.nms_ref == nms_ref, Incident.category == category, Incident.opened_at >= cutoff))
        .first()
    )
    return existing


@router.post("/librenms")
@limiter.limit("30/minute")
async def librenms(request: Request, db: Session = Depends(get_db)):
    _verify_source(request)
    raw = await request.body()
    _verify_hmac(request, raw)
    data = await request.json()
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
@limiter.limit("30/minute")
async def zabbix(request: Request, db: Session = Depends(get_db)):
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

