import hmac
import hashlib
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.incident import Incident
from app.models.device import Device
from sqlalchemy import text


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# LibreNMS configured alert transport
# Example JSON fields used: hostname, state, severity, rule, alert_id, timestamp, msg
def _verify_hmac(request: Request, body: bytes, secret: str):
    sig = request.headers.get("X-Signature")
    if not sig:
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, digest)


def _ip_allowed(request: Request, allowlist: list[str]):
    client = request.client.host if request.client else None
    return (not allowlist) or (client in allowlist)


def _dedup_key(prefix: str, device_id: str | None, category: str, state: str, window_min: int = 30):
    return f"{prefix}:{device_id}:{category}:{state}:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"


@router.post("/librenms")
async def librenms(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    allowlist = os.getenv("LIBRENMS_IP_ALLOW", "127.0.0.1").split(",")
    secret = os.getenv("LIBRENMS_HMAC_SECRET", "librenms-secret")
    if not _ip_allowed(request, allowlist) or not _verify_hmac(request, raw, secret):
        raise HTTPException(403, "Forbidden")
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

    if state == "alert":
        # Dedup within 30 minutes by device+category
        if device:
            exists = (
                db.execute(
                    text(
                        """
                        select id from incidents
                        where device_id = :d and category = :c and status in ('Open','Acknowledged')
                        and opened_at > now() - interval '30 minutes'
                        limit 1
                        """
                    ),
                    {"d": str(device.id), "c": category},
                )
                .scalar()
            )
            if exists:
                return {"ok": True, "incident_id": str(exists), "dedup": True}

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
    else:
        # Clear handler: resolve by nms_ref
        db.execute(
            text(
                """
                update incidents set status = 'Resolved', resolved_at = now()
                where nms_ref = :ref and status in ('Open','Acknowledged')
                """
            ),
            {"ref": f"librenms:{alert_id}"},
        )
        db.commit()
        return {"ok": True, "cleared": True}


# Zabbix webhook
# Expect { "host": "OLT-01", "severity": "Disaster|High|Average|Warning|Info", "event_id": "123", "problem": true, "name": "Link down", "message": "..." }
@router.post("/zabbix")
async def zabbix(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    allowlist = os.getenv("ZABBIX_IP_ALLOW", "127.0.0.1").split(",")
    secret = os.getenv("ZABBIX_HMAC_SECRET", "zabbix-secret")
    if not _ip_allowed(request, allowlist) or not _verify_hmac(request, raw, secret):
        raise HTTPException(403, "Forbidden")
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

    if problem:
        # Dedup within 30 minutes
        if device:
            exists = (
                db.execute(
                    text(
                        """
                        select id from incidents
                        where device_id = :d and category = 'Device' and status in ('Open','Acknowledged')
                        and opened_at > now() - interval '30 minutes'
                        limit 1
                        """
                    ),
                    {"d": str(device.id)},
                )
                .scalar()
            )
            if exists:
                return {"ok": True, "incident_id": str(exists), "dedup": True}
        inc = Incident(
            device_id=device.id if device else None,
            pon_id=device.pon_id if device else None,
            severity=severity_map.get(sev, "P3"),
            category="Device",
            title=f"{host} {name}",
            description=msg,
            status="Open",
            nms_ref=f"zabbix:{event_id}",
            opened_at=datetime.now(timezone.utc),
        )
        db.add(inc)
        db.commit()
        return {"ok": True, "incident_id": str(inc.id)}
    else:
        # Clear handler: resolve existing incidents
        db.execute(
            text(
                """
                update incidents set status = 'Resolved', resolved_at = now()
                where nms_ref = :ref and status in ('Open','Acknowledged')
                """
            ),
            {"ref": f"zabbix:{event_id}"},
        )
        db.commit()
        return {"ok": True, "cleared": True}

