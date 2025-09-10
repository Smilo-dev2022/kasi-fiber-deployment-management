from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.deps import get_db, require_roles
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceOut


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=List[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    role: Optional[str] = Query(None),
    pon_id: Optional[str] = Query(None),
):
    q = db.query(Device)
    if role:
        q = q.filter(Device.role == role)
    if pon_id:
        q = q.filter(Device.pon_id == UUID(pon_id))
    return q.order_by(Device.name).all()


@router.post("", response_model=DeviceOut, dependencies=[Depends(require_roles("ADMIN", "PM"))])
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    d = Device(**payload.dict())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.patch("/{device_id}", response_model=DeviceOut, dependencies=[Depends(require_roles("ADMIN", "PM"))])
def update_device(device_id: str, payload: DeviceCreate, db: Session = Depends(get_db)):
    d = db.get(Device, UUID(device_id))
    if not d:
        raise HTTPException(404, "Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d

