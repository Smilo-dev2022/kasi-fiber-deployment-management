import os
import hmac
import hashlib
import re
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db, require_roles
from app.core.rate_limit import rate_limit
from app.models.device import Device, DeviceConfig, GoldenTemplate
from app.models.incident import Incident


router = APIRouter(prefix="/configs", tags=["configs"])


def _verify_hmac(request: Request, body: bytes):
    secret = os.getenv("OXIDIZED_HMAC_SECRET")
    if not secret:
        return
    sig = request.headers.get("X-Signature") or request.headers.get("X-Hub-Signature")
    if not sig:
        raise HTTPException(401, "Missing signature")
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, mac):
        raise HTTPException(401, "Invalid signature")


@router.post("/oxidized")
async def oxidized_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    _verify_hmac(request, raw)
    data = await request.json()
    # Expect at least: {"name": "OLT-01", "config": "..."}
    name = data.get("name")
    config_text = data.get("config")
    if not name or not config_text:
        raise HTTPException(400, "name and config required")

    device = db.query(Device).filter(Device.name == name).first()
    if not device:
        raise HTTPException(404, "Device not found")

    cfg = DeviceConfig(
        id=uuid4(),
        device_id=device.id,
        running_config=config_text,
        collected_at=datetime.now(timezone.utc),
        hash_sha256=hashlib.sha256(config_text.encode()).hexdigest(),
    )
    db.add(cfg)
    db.flush()

    # Diff/policy check against golden template by device role
    gt = db.query(GoldenTemplate).filter(GoldenTemplate.device_role == device.role).first()
    out_of_policy = []
    if gt and gt.policy_regex_deny:
        for line in config_text.splitlines():
            if re.search(gt.policy_regex_deny, line):
                out_of_policy.append(line)

    if out_of_policy:
        inc = Incident(
            device_id=device.id,
            pon_id=device.pon_id,
            severity="P3",
            category="Config",
            title=f"Out-of-policy config on {device.name}",
            description="\n".join(out_of_policy[:50]),
            status="Open",
            opened_at=datetime.now(timezone.utc),
            nms_ref=f"oxidized:{cfg.id}",
        )
        db.add(inc)

    db.commit()
    return {"ok": True, "device_id": str(device.id), "config_id": str(cfg.id), "violations": len(out_of_policy)}

