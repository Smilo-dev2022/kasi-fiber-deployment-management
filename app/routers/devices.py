from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.device import Device


router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceIn(BaseModel):
    kind: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    mgmt_ip: Optional[str] = None
    site: Optional[str] = None
    tenant: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    pon_id: Optional[str] = None


@router.post("/", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_device(payload: DeviceIn, db: Session = Depends(get_db)):
    data = payload.dict(exclude_unset=True)
    dev = Device(id=uuid4(), **data)
    db.add(dev)
    db.commit()
    return {"id": str(dev.id)}


@router.get("/", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def list_devices(kind: Optional[str] = None, site: Optional[str] = None, tenant: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Device)
    if kind:
        q = q.filter(Device.kind == kind)
    if site:
        q = q.filter(Device.site == site)
    if tenant:
        q = q.filter(Device.tenant == tenant)
    rows = q.limit(500).all()
    return [
        {
            "id": str(r.id),
            "kind": r.kind,
            "vendor": r.vendor,
            "model": r.model,
            "serial": r.serial,
            "mgmt_ip": r.mgmt_ip,
            "site": r.site,
            "tenant": r.tenant,
            "role": r.role,
            "status": r.status,
            "pon_id": str(r.pon_id) if r.pon_id else None,
        }
        for r in rows
    ]


@router.get("/{device_id}", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE"))])
def get_device(device_id: str, db: Session = Depends(get_db)):
    dev = db.get(Device, UUID(device_id))
    if not dev:
        raise HTTPException(404, "Not found")
    return {
        "id": str(dev.id),
        "kind": dev.kind,
        "vendor": dev.vendor,
        "model": dev.model,
        "serial": dev.serial,
        "mgmt_ip": dev.mgmt_ip,
        "site": dev.site,
        "tenant": dev.tenant,
        "role": dev.role,
        "status": dev.status,
        "pon_id": str(dev.pon_id) if dev.pon_id else None,
        "last_seen_at": dev.last_seen_at,
        "uptime_seconds": dev.uptime_seconds,
    }


@router.patch("/{device_id}", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def update_device(device_id: str, payload: DeviceIn, db: Session = Depends(get_db)):
    dev = db.get(Device, UUID(device_id))
    if not dev:
        raise HTTPException(404, "Not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(dev, k, v)
    db.commit()
    return {"ok": True}


@router.delete("/{device_id}", dependencies=[Depends(require_roles("ADMIN"))])
def delete_device(device_id: str, db: Session = Depends(get_db)):
    dev = db.get(Device, UUID(device_id))
    if not dev:
        raise HTTPException(404, "Not found")
    db.delete(dev)
    db.commit()
    return {"ok": True}

