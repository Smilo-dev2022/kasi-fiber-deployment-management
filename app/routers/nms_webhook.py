from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.deps import get_db
from app.models.incident import Incident
from app.models.device import Device


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/librenms")
async def librenms(request: Request, db: Session = Depends(get_db)):
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


@router.post("/zabbix")
async def zabbix(request: Request, db: Session = Depends(get_db)):
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

