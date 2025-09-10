import os
import hmac
import hashlib
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from app.core.deps import get_db
from app.models.incident import Incident
from app.models.device import Device
from app.models.pon import PON


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# LibreNMS configured alert transport
# Example JSON fields used: hostname, state, severity, rule, alert_id, timestamp, msg
def _require_ip_and_hmac(request: Request, body: bytes):
    allowlist = os.getenv("NMS_IP_ALLOWLIST", "").split(",")
    allowlist = [ip.strip() for ip in allowlist if ip.strip()]
    if allowlist:
        client_ip = request.client.host if request.client else None
        if client_ip not in allowlist:
            raise HTTPException(403, "IP not allowed")
    secret = os.getenv("NMS_HMAC_SECRET")
    if secret:
        sig = request.headers.get("X-Signature")
        if not sig:
            raise HTTPException(401, "Missing signature")
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, digest):
            raise HTTPException(401, "Invalid signature")


def _auto_assign_and_due(db: Session, pon_id, severity: str):
    if not pon_id:
        return None, None
    # find assignment for Maintenance scope by PON or ward
    ward = None
    if pon_id:
        row = db.execute(text("select ward from pons where id = :id"), {"id": str(pon_id)}).first()
        ward = row[0] if row else None
    asg = (
        db.execute(
            text(
                """
            select org_id from assignments
            where step_type = 'Maintenance'
            and (
              (pon_id is not null and pon_id = :pon)
              or (ward is not null and ward = :ward)
            )
            order by pon_id is null, ward is null
            limit 1
            """
            ),
            {"pon": str(pon_id), "ward": ward},
        ).first()
    )
    org_id = asg[0] if asg else None
    # SLA minutes from contracts for that org/ward
    if org_id:
        sev_col = {"P1": "sla_p1_minutes", "P2": "sla_p2_minutes", "P3": "sla_p3_minutes", "P4": "sla_p4_minutes"}.get(
            severity, "sla_p3_minutes"
        )
        row = (
            db.execute(
                text(
                    f"""
                select {sev_col} from contracts
                where org_id = :org and scope = 'Maintenance' and (wards is null or :ward = any(string_to_array(wards, ',')))
                order by valid_from desc nulls last
                limit 1
                """
                ),
                {"org": str(org_id), "ward": ward},
            ).first()
        )
        sla = row[0] if row and row[0] is not None else None
    else:
        sla = None
    due_at = datetime.now(timezone.utc) + timedelta(minutes=sla) if sla else None
    return org_id, due_at


def _dedup_recent(db: Session, device_id, category: str):
    since = datetime.now(timezone.utc) - timedelta(minutes=30)
    q = (
        db.query(Incident)
        .filter(Incident.device_id == device_id)
        .filter(Incident.category == category)
        .filter(Incident.opened_at >= since)
        .filter(Incident.status.in_(["Open", "Acknowledged"]))
    )
    return q.first()


@router.post("/librenms")
async def librenms(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    _require_ip_and_hmac(request, raw)
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
    severity = severity_map.get(sev, "P3")

    # Clear handler
    if state and state.lower() in ("clear", "resolved", "recovery", "ok"):
        ref = f"librenms:{alert_id}"
        row = (
            db.execute(
                text("select id from incidents where nms_ref = :ref and status in ('Open','Acknowledged') order by opened_at desc limit 1"),
                {"ref": ref},
            ).first()
        )
        if row:
            db.execute(
                text("update incidents set status = 'Resolved', resolved_at = now() where id = :id"),
                {"id": str(row[0])},
            )
            db.commit()
            return {"ok": True, "incident_id": str(row[0]), "resolved": True}
        return {"ok": True, "resolved": False}

    # Dedup within 30 minutes
    existing = _dedup_recent(db, device.id if device else None, category) if device else None
    if existing:
        # append message as audit note
        db.execute(
            text(
                "insert into incident_audits (id, incident_id, action, notes) values (gen_random_uuid(), :iid, 'update', :notes)"
            ),
            {"iid": str(existing.id), "notes": msg[:500]},
        )
        db.commit()
        return {"ok": True, "incident_id": str(existing.id), "dedup": True}

    assigned_org_id, due_at = _auto_assign_and_due(db, device.pon_id if device else None, severity)
    inc = Incident(
        device_id=device.id if device else None,
        pon_id=device.pon_id if device else None,
        severity=severity,
        category=category,
        title=title,
        description=msg,
        status="Open",
        nms_ref=f"librenms:{alert_id}",
        opened_at=datetime.now(timezone.utc),
        assigned_org_id=assigned_org_id,
        severity_sla_minutes=None,
        due_at=due_at,
    )
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}


# Zabbix webhook
# Expect { "host": "OLT-01", "severity": "Disaster|High|Average|Warning|Info", "event_id": "123", "problem": true, "name": "Link down", "message": "..." }
@router.post("/zabbix")
async def zabbix(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    _require_ip_and_hmac(request, raw)
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
    severity = severity_map.get(sev, "P3")

    # Resolve existing on clear
    if not problem:
        ref = f"zabbix:{event_id}"
        row = (
            db.execute(
                text("select id from incidents where nms_ref = :ref and status in ('Open','Acknowledged') order by opened_at desc limit 1"),
                {"ref": ref},
            ).first()
        )
        if row:
            db.execute(
                text("update incidents set status = 'Resolved', resolved_at = now() where id = :id"),
                {"id": str(row[0])},
            )
            db.commit()
            return {"ok": True, "incident_id": str(row[0]), "resolved": True}
        return {"ok": True, "resolved": False}

    # Dedup
    existing = _dedup_recent(db, device.id if device else None, "Device") if device else None
    if existing:
        db.execute(
            text(
                "insert into incident_audits (id, incident_id, action, notes) values (gen_random_uuid(), :iid, 'update', :notes)"
            ),
            {"iid": str(existing.id), "notes": msg[:500]},
        )
        db.commit()
        return {"ok": True, "incident_id": str(existing.id), "dedup": True}

    assigned_org_id, due_at = _auto_assign_and_due(db, device.pon_id if device else None, severity)
    inc = Incident(
        device_id=device.id if device else None,
        pon_id=device.pon_id if device else None,
        severity=severity,
        category="Device",
        title=f"{host} {name}",
        description=msg,
        status=status,
        nms_ref=f"zabbix:{event_id}",
        opened_at=datetime.now(timezone.utc),
        resolved_at=None,
        assigned_org_id=assigned_org_id,
        severity_sla_minutes=None,
        due_at=due_at,
    )
    db.add(inc)
    db.commit()
    return {"ok": True, "incident_id": str(inc.id)}

