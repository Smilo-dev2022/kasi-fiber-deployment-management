from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.deps import get_db
from app.models.incident import Incident
from app.models.device import Device
from sqlalchemy import text
import hmac
import hashlib
import os


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# LibreNMS configured alert transport
# Example JSON fields used: hostname, state, severity, rule, alert_id, timestamp, msg
def _verify_source(request: Request, body_bytes: bytes) -> None:
    # IP allow list (optional via env WEBHOOK_IP_ALLOW_LIST=ip1,ip2)
    allow_env = os.getenv("WEBHOOK_IP_ALLOW_LIST", "")
    allow = [ip.strip() for ip in allow_env.split(",") if ip.strip()]
    if allow:
        peer = request.client.host if request.client else None
        if peer not in allow:
            raise HTTPException(403, "Source IP not allowed")
    # HMAC (optional)
    secret = os.getenv("NMS_HMAC_SECRET")
    sig = request.headers.get("X-Hub-Signature")
    if secret and sig:
        digest = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(f"sha256={digest}", sig):
            raise HTTPException(403, "Invalid HMAC signature")


def _dedup(db: Session, device_id, category: str, state: str, window_min: int = 30) -> bool:
    # If an open incident of same category on device exists in last window, skip creating
    row = (
        db.execute(
            text(
                """
        select 1 from incidents
        where device_id = :d and category = :c and status in ('Open','Acknowledged','Monitoring')
          and opened_at > now() - (:w || ' minutes')::interval
        limit 1
      """
            ),
            {"d": str(device_id) if device_id else None, "c": category, "w": window_min},
        )
        .first()
    )
    return bool(row)


def _auto_assign(db: Session, device: Device | None, category: str) -> tuple[str | None, int | None]:
    # Map category to step and find assignment by PON
    category_to_step = {
        "Device": "Maintenance",
        "Power": "Maintenance",
        "Optical": "Splicing",
        "Link": "Maintenance",
    }
    step = category_to_step.get(category, "Maintenance")
    pon_id = str(device.pon_id) if device and device.pon_id else None
    row = (
        db.execute(
            text("select org_id::text from assignments where pon_id = :p and step = :s order by created_at desc limit 1"),
            {"p": pon_id, "s": step},
        )
        .mappings()
        .first()
    )
    org_id = row["org_id"] if row else None
    # SLA minutes by severity via contract
    sev_map = {"P1": "sla_p1_minutes", "P2": "sla_p2_minutes", "P3": "sla_p3_minutes", "P4": "sla_p4_minutes"}
    sev_field = sev_map.get("P3")
    sla = None
    if org_id:
        srow = (
            db.execute(
                text(f"select {sev_field} as mins from contracts where org_id = :o order by valid_from desc limit 1"),
                {"o": org_id},
            )
            .mappings()
            .first()
        )
        sla = srow["mins"] if srow else None
    return org_id, sla


@router.post("/librenms")
async def librenms(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    _verify_source(request, body)
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
    # clear handler
    if state.lower() in ("clear", "ok", "recover"):
        if device:
            db.execute(
                text(
                    """
            update incidents set status = 'Resolved', resolved_at = now()
            where device_id = :d and category = 'Device' and status in ('Open','Acknowledged','Monitoring')
          """
                ),
                {"d": str(device.id)},
            )
            db.commit()
        return {"ok": True, "resolved": True}

    if _dedup(db, device.id if device else None, category, state):
        return {"ok": True, "dedup": True}

    assigned_org_id, sla_mins = _auto_assign(db, device, category)
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
    if assigned_org_id:
        inc.assigned_org_id = assigned_org_id
        if sla_mins:
            inc.severity_sla_minutes = int(sla_mins)
            inc.due_at = datetime.now(timezone.utc) + timedelta(minutes=int(sla_mins))
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}


# Zabbix webhook
# Expect { "host": "OLT-01", "severity": "Disaster|High|Average|Warning|Info", "event_id": "123", "problem": true, "name": "Link down", "message": "..." }
@router.post("/zabbix")
async def zabbix(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    _verify_source(request, body)
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
    # Clear handlers: if recovery event, resolve any open incident for this device/category
    if not problem:
        db.execute(
            text(
                """
        update incidents set status = 'Resolved', resolved_at = now()
        where device_id = :d and category = 'Device' and status in ('Open','Acknowledged','Monitoring')
      """
            ),
            {"d": str(device.id) if device else None},
        )
        db.commit()
        return {"ok": True, "resolved": True}

    if _dedup(db, device.id if device else None, "Device", "alert"):
        return {"ok": True, "dedup": True}

    assigned_org_id, sla_mins = _auto_assign(db, device, "Device")
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
    if assigned_org_id:
        inc.assigned_org_id = assigned_org_id
        if sla_mins:
            inc.severity_sla_minutes = int(sla_mins)
            inc.due_at = datetime.now(timezone.utc) + timedelta(minutes=int(sla_mins))
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}

