import os
from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse


router = APIRouter(prefix="/nms", tags=["nms"])

ALLOWED_IPS = {ip.strip() for ip in os.getenv("NMS_WHITELIST_IPS", "").split(",") if ip.strip()}
WEBHOOK_SECRET = os.getenv("NMS_WEBHOOK_SECRET")


def _client_ip(request: Request) -> str:
    # Respect common proxy headers if present
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    ip = _client_ip(request)
    if ALLOWED_IPS and ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="Forbidden IP")
    if WEBHOOK_SECRET:
        auth = request.headers.get("x-webhook-secret") or request.headers.get("authorization", "").replace("Bearer ", "")
        if auth != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid secret")

    payload = await request.json()
    # Normalize common LibreNMS/Zabbix style payloads
    event = payload.get("event") or payload.get("trigger") or payload.get("type") or "unknown"
    device = payload.get("hostname") or payload.get("device") or payload.get("host")
    state = payload.get("state") or payload.get("status") or payload.get("severity")
    note = payload.get("message") or payload.get("summary") or payload

    # TODO: Map to incidents table when implemented
    return JSONResponse({"ok": True, "event": event, "device": device, "state": state, "note": note})


@router.post("/test")
async def send_test() -> dict:
    return {
        "ok": True,
        "examples": [
            {"event": "device_down", "hostname": "olt-ward1-01", "state": "critical", "message": "Device is down"},
            {"event": "los", "hostname": "olt-ward1-01", "state": "warning", "message": "Optical LOS on PON1"},
            {"event": "low_power", "hostname": "olt-ward1-01", "state": "warning", "message": "RX power -28 dBm"},
            {"event": "clear", "hostname": "olt-ward1-01", "state": "ok", "message": "Recovered"},
        ],
    }

