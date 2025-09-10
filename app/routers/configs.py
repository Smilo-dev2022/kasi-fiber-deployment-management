import os
import hmac
import hashlib
from collections import deque
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_scoped_db
from app.models.configs import DeviceConfig, GoldenTemplate
from app.models.device import Device
from app.models.maint import MaintWindow
from app.models.incident import Incident
import uuid


router = APIRouter(prefix="/configs", tags=["configs"])


_RATE_BUCKETS: dict[str, deque] = {}


def _rate_limit(request: Request, limit_per_minute: int = 60):
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}:{request.url.path}"
    q = _RATE_BUCKETS.setdefault(key, deque())
    now_ts = datetime.now(timezone.utc).timestamp()
    while q and now_ts - q[0] > 60:
        q.popleft()
    if len(q) >= limit_per_minute:
        raise HTTPException(429, "Rate limit exceeded")
    q.append(now_ts)


def _verify_source(request: Request):
    allow_ips = os.getenv("OXIDIZED_ALLOW_IPS", "").split(",")
    allow_ips = [ip.strip() for ip in allow_ips if ip.strip()]
    if allow_ips:
        ip = request.client.host if request.client else None
        if ip not in allow_ips:
            raise HTTPException(403, "IP not allowed")


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


def _suppressed(db: Session, device: Device | None):
    now = datetime.now(timezone.utc)
    q = db.query(MaintWindow).filter(MaintWindow.start_at <= now).filter(MaintWindow.end_at >= now)
    if device:
        dev_match = q.filter(MaintWindow.scope == "device").filter(MaintWindow.target_id == device.id).first()
        if dev_match:
            return True
        if device.pon_id:
            pon_match = q.filter(MaintWindow.scope == "pon").filter(MaintWindow.target_id == device.pon_id).first()
            if pon_match:
                return True
    glob = q.filter(MaintWindow.scope == "global").first()
    return bool(glob)


@router.post("/oxidized")
async def oxidized_webhook(request: Request, db: Session = Depends(get_scoped_db)):
    _rate_limit(request)
    raw = await request.body()
    _verify_source(request)
    _verify_hmac(request, raw)
    data = await request.json()
    # Expected payload subset: { "node": "OLT-01", "time": 1690000000, "model": "ios", "group": "core", "commitref": "abcd", "diff": "...", "config": "..." }
    node = data.get("node")
    content = data.get("config") or data.get("contents")
    if not node or not content:
        raise HTTPException(400, "Missing node/config")
    device = db.query(Device).filter(Device.name == node).first()
    if not device:
        raise HTTPException(404, "Device not found")
    if _suppressed(db, device):
        return {"ok": True, "suppressed": True}
    sha = hashlib.sha256(content.encode()).hexdigest()
    dc = DeviceConfig(
        id=uuid.uuid4(),
        device_id=device.id,
        source="oxidized",
        collected_at=datetime.now(timezone.utc),
        content=content,
        sha256=sha,
        version=str(data.get("commitref") or "") or None,
    )
    db.add(dc)
    # Diff against golden template if available
    tmpl = (
        db.query(GoldenTemplate)
        .filter((GoldenTemplate.role == device.role) | (GoldenTemplate.role.is_(None)))
        .filter((GoldenTemplate.vendor == device.vendor) | (GoldenTemplate.vendor.is_(None)))
        .filter((GoldenTemplate.model == device.model) | (GoldenTemplate.model.is_(None)))
        .order_by(GoldenTemplate.role.desc().nullslast())
        .first()
    )
    out_of_policy = False
    if tmpl:
        # naive line-by-line policy: all non-empty non-comment lines in template must exist in config
        wanted = [ln.strip() for ln in tmpl.template.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        have = set([ln.strip() for ln in content.splitlines()])
        missing = [ln for ln in wanted if ln not in have]
        out_of_policy = len(missing) > 0
    # Create a P3 Config incident if out of policy and no recent open incident
    if out_of_policy:
        ref = f"config:{str(device.id)}:out_of_policy"
        existing = (
            db.query(Incident)
            .filter(Incident.nms_ref == ref)
            .filter(Incident.status != "Closed")
            .first()
        )
        if not existing:
            inc = Incident(
                device_id=device.id,
                pon_id=device.pon_id,
                severity="P3",
                category="Config",
                title=f"{device.name} config out of policy",
                description="Golden template mismatch detected",
                status="Open",
                nms_ref=ref,
                opened_at=datetime.now(timezone.utc),
            )
            db.add(inc)
    db.commit()
    return {"ok": True, "device_id": str(device.id), "stored": True, "out_of_policy": out_of_policy}

