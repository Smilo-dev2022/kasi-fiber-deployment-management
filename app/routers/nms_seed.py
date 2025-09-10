from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4

from app.core.deps import get_db, require_roles
from app.models.nms import Device, Port, ONU, OpticalBaseline


router = APIRouter(prefix="/nms", tags=["nms"])


class DeviceIn(BaseModel):
    name: str
    hostname: str
    device_type: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    ward: Optional[str] = None
    pon_id: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None


class PortIn(BaseModel):
    device_hostname: str
    name: str
    if_index: Optional[int] = None
    port_type: Optional[str] = None


class ONUIn(BaseModel):
    device_hostname: str
    port_name: Optional[str] = None
    pon_id: Optional[str] = None
    serial: str
    name: Optional[str] = None


class BaselineIn(BaseModel):
    device_hostname: Optional[str] = None
    port_name: Optional[str] = None
    onu_serial: Optional[str] = None
    kind: str
    baseline_dbm: float
    source: Optional[str] = "seed"


@router.post("/devices", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_devices(payload: List[DeviceIn], db: Session = Depends(get_db)):
    created = 0
    for d in payload:
        existing = db.query(Device).filter(Device.hostname == d.hostname).first()
        if existing:
            continue
        rec = Device(
            id=uuid4(),
            name=d.name,
            hostname=d.hostname,
            device_type=d.device_type,
            vendor=d.vendor,
            model=d.model,
            serial=d.serial,
            ward=d.ward,
            gps_lat=d.gps_lat,
            gps_lng=d.gps_lng,
        )
        db.add(rec)
        created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.post("/ports", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_ports(payload: List[PortIn], db: Session = Depends(get_db)):
    created = 0
    for p in payload:
        device = db.query(Device).filter(Device.hostname == p.device_hostname).first()
        if not device:
            raise HTTPException(400, f"Device not found: {p.device_hostname}")
        exists = (
            db.query(Port)
            .filter(Port.device_id == device.id, Port.name == p.name)
            .first()
        )
        if exists:
            continue
        row = Port(
            id=uuid4(),
            device_id=device.id,
            name=p.name,
            if_index=p.if_index,
            port_type=p.port_type,
        )
        db.add(row)
        created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.post("/onus", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_onus(payload: List[ONUIn], db: Session = Depends(get_db)):
    created = 0
    for o in payload:
        device = db.query(Device).filter(Device.hostname == o.device_hostname).first()
        if not device:
            raise HTTPException(400, f"Device not found: {o.device_hostname}")
        port_id = None
        if o.port_name:
            port = db.query(Port).filter(Port.device_id == device.id, Port.name == o.port_name).first()
            port_id = port.id if port else None
        exists = db.query(ONU).filter(ONU.device_id == device.id, ONU.serial == o.serial).first()
        if exists:
            continue
        row = ONU(
            id=uuid4(),
            device_id=device.id,
            port_id=port_id,
            pon_id=o.pon_id,
            serial=o.serial,
            name=o.name,
        )
        db.add(row)
        created += 1
    db.commit()
    return {"ok": True, "created": created}


@router.post("/optical/baselines", dependencies=[Depends(require_roles("ADMIN", "PM"))])
def add_baselines(payload: List[BaselineIn], db: Session = Depends(get_db)):
    created = 0
    for b in payload:
        device = None
        if b.device_hostname:
            device = db.query(Device).filter(Device.hostname == b.device_hostname).first()
        port = None
        if device and b.port_name:
            port = db.query(Port).filter(Port.device_id == device.id, Port.name == b.port_name).first()
        onu = None
        if b.onu_serial:
            onu = db.query(ONU).filter(ONU.serial == b.onu_serial).first()
        rec = OpticalBaseline(
            id=uuid4(),
            device_id=(device.id if device else None),
            port_id=(port.id if port else None),
            onu_id=(onu.id if onu else None),
            kind=b.kind,
            baseline_dbm=b.baseline_dbm,
            source=b.source,
        )
        db.add(rec)
        created += 1
    db.commit()
    return {"ok": True, "created": created}

