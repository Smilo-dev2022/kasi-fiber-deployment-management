from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
import json
from datetime import datetime, timezone, timedelta

from app.core.deps import get_db
from app.core.security import verify_webhook_hmac, enforce_ip_whitelist, get_client_ip
from app.core.ratelimit import enforce_webhook_rate_limit
from app.core.settings import get_settings
from app.models.nms import Incident, Device, Port, ONU, WebhookEvent


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def map_severity(nms_severity: str) -> str:
    s = (nms_severity or "").lower()
    if s in ("critical", "disaster", "high"):
        return "P1"
    if s in ("major", "average"):
        return "P2"
    if s in ("minor", "warning"):
        return "P3"
    return "P4"


def dedup_key(parts: list[str]) -> str:
    return "|".join([p for p in parts if p])


def within_maintenance(db: Session, device_id: str | None, ward: str | None) -> bool:
    # Suppress incidents during maintenance windows
    now = datetime.now(timezone.utc)
    q = text(
        """
        select 1 from maintenance_windows mw
        where mw.start_ts <= :now and mw.end_ts >= :now and mw.status = 'Approved'
        and (
          mw.scope_type = 'GLOBAL' or
          (mw.scope_type = 'WARD' and mw.ward = :ward) or
          (mw.scope_type = 'DEVICE' and mw.device_id = :device_id)
        )
        limit 1
        """
    )
    row = db.execute(q, {"now": now, "ward": ward, "device_id": device_id}).first()
    return bool(row)


@router.post("/librenms")
async def webhook_librenms(request: Request, db: Session = Depends(get_db)):
    enforce_ip_whitelist(request)
    ip = get_client_ip(request)
    enforce_webhook_rate_limit(ip, "/webhooks/librenms")

    body = await request.body()
    ok_hmac = verify_webhook_hmac(request, body)

    payload = {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        pass

    db.add(
        WebhookEvent(
            id=uuid4(),
            source="LibreNMS",
            received_ip=ip,
            hmac_valid=ok_hmac,
            payload=json.dumps(payload)[:65535],
        )
    )
    db.commit()

    if not ok_hmac:
        raise HTTPException(401, "Invalid signature")

    # Expected LibreNMS fields
    hostname = payload.get("hostname") or payload.get("host")
    state = payload.get("state")  # up/down/clear
    alert = payload.get("alert") or {}
    severity = map_severity(alert.get("severity") or payload.get("severity"))
    rule = alert.get("rule") or payload.get("rule")
    port_name = payload.get("ifName") or payload.get("port")
    category = "DeviceDown"
    description = alert.get("msg") or payload.get("msg") or json.dumps(payload)[:200]

    # Device mapping
    device = db.query(Device).filter(Device.hostname == hostname).first()
    device_id = str(device.id) if device else None
    ward = device.ward if device else None

    # Port mapping
    port_id = None
    if device and port_name:
        port = db.query(Port).filter(Port.device_id == device.id, Port.name == port_name).first()
        if port:
            port_id = str(port.id)

    if state in ("up", "clear"):
        # Close matching incidents
        key = dedup_key([hostname, port_name, rule])
        db.execute(
            text(
                "update incidents set status='Resolved', resolved_at=now(), ttr_seconds=extract(epoch from (now()-opened_at)) where status='Open' and dedup_key=:k"
            ),
            {"k": key},
        )
        db.commit()
        return {"ok": True, "closed": True}

    if state == "down":
        if within_maintenance(db, device_id, ward):
            return {"ok": True, "suppressed": True}
        key = dedup_key([hostname, port_name, rule])
        # Dedup: upsert open incident
        ins_sql = text(
            """
            insert into incidents (id, tenant_id, category, severity, status, dedup_key, description, device_id, port_id, ward)
            values (gen_random_uuid(), :tenant, :cat, :sev, 'Open', :key, :desc, :device_id::uuid, :port_id::uuid, :ward)
            on conflict (dedup_key) do update set severity=excluded.severity, description=excluded.description
            returning id
            """
        )
        tenant = get_settings().DEFAULT_TENANT_ID
        row = db.execute(
            ins_sql,
            {
                "tenant": tenant,
                "cat": category,
                "sev": severity,
                "key": key,
                "desc": description,
                "device_id": device_id,
                "port_id": port_id,
                "ward": ward,
            },
        ).first()
        db.commit()
        return {"ok": True, "incident_id": str(row[0]) if row else None}

    return {"ok": True}


@router.post("/zabbix")
async def webhook_zabbix(request: Request, db: Session = Depends(get_db)):
    enforce_ip_whitelist(request)
    ip = get_client_ip(request)
    enforce_webhook_rate_limit(ip, "/webhooks/zabbix")

    body = await request.body()
    ok_hmac = verify_webhook_hmac(request, body)
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        payload = {}

    db.add(
        WebhookEvent(
            id=uuid4(),
            source="Zabbix",
            received_ip=ip,
            hmac_valid=ok_hmac,
            payload=json.dumps(payload)[:65535],
        )
    )
    db.commit()

    if not ok_hmac:
        raise HTTPException(401, "Invalid signature")

    # Zabbix fields per media/script payload
    hostname = payload.get("host") or payload.get("hostname")
    event = payload.get("event") or {}
    status = (event.get("status") or payload.get("status") or "").lower()  # problem/resolved
    severity = map_severity(payload.get("severity") or event.get("severity"))
    port_name = payload.get("port")
    category = payload.get("category") or ("OpticalLow" if "optical" in (payload.get("trigger") or "").lower() else "DeviceDown")
    description = payload.get("message") or payload.get("trigger") or json.dumps(payload)[:200]

    device = db.query(Device).filter(Device.hostname == hostname).first()
    device_id = str(device.id) if device else None
    ward = device.ward if device else None

    port_id = None
    if device and port_name:
        port = db.query(Port).filter(Port.device_id == device.id, Port.name == port_name).first()
        if port:
            port_id = str(port.id)

    key = dedup_key([hostname, port_name, category])

    if status in ("resolved", "ok", "clear"):
        db.execute(
            text(
                "update incidents set status='Resolved', resolved_at=now(), ttr_seconds=extract(epoch from (now()-opened_at)) where status='Open' and dedup_key=:k"
            ),
            {"k": key},
        )
        db.commit()
        return {"ok": True, "closed": True}

    if status in ("problem", "down"):
        if within_maintenance(db, device_id, ward):
            return {"ok": True, "suppressed": True}
        tenant = get_settings().DEFAULT_TENANT_ID
        ins = text(
            """
            insert into incidents (id, tenant_id, category, severity, status, dedup_key, description, device_id, port_id, ward)
            values (gen_random_uuid(), :tenant, :cat, :sev, 'Open', :key, :desc, :device_id::uuid, :port_id::uuid, :ward)
            on conflict (dedup_key) do update set severity=excluded.severity, description=excluded.description
            returning id
            """
        )
        row = db.execute(
            ins,
            {
                "tenant": tenant,
                "cat": category,
                "sev": severity,
                "key": key,
                "desc": description,
                "device_id": device_id,
                "port_id": port_id,
                "ward": ward,
            },
        ).first()
        db.commit()
        return {"ok": True, "incident_id": str(row[0]) if row else None}

    return {"ok": True}

