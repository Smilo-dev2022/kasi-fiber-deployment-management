import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.routers import tasks as tasks_router
from app.routers import cac as cac_router
from app.routers import pons_geofence as pons_geo_router
from app.routers import photos_validate as photos_val_router
from app.routers import assets as assets_router
from app.routers import reports as reports_router
from app.routers import rate_cards as rate_router
from app.routers import pay_sheets as pays_router
from app.routers import photos_upload_hook as photos_upload_router
from app.scheduler import init_jobs
from app.routers import nms_webhook as nms_router
from app.routers import admin_seed as seed_router


logger = logging.getLogger("app")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


class UploadSizeLimitMiddleware:
    def __init__(self, app: FastAPI, max_mb: int) -> None:
        self.app = app
        self.max_bytes = max_mb * 1024 * 1024

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers") or [])
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    resp = JSONResponse({"detail": "Payload too large"}, status_code=413)
                    return await resp(scope, receive, send)
            except Exception:
                pass
        return await self.app(scope, receive, send)


app = FastAPI()

# CORS
cors_allowlist = [o.strip() for o in os.getenv("CORS_ALLOWLIST", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowlist,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload caps (10 MB default)
max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "10"))
app.add_middleware(UploadSizeLimitMiddleware, max_mb=max_upload_mb)

app.include_router(tasks_router.router)
app.include_router(cac_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)
app.include_router(photos_upload_router.router)
app.include_router(nms_router.router)
app.include_router(seed_router.router)

@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/ready")
async def ready(request: Request) -> JSONResponse:
    # Simple DB probe
    try:
        from sqlalchemy import text
        from app.core.deps import SessionLocal

        with SessionLocal() as db:
            db.execute(text("select 1"))
    except Exception as exc:  # pragma: no cover
        logger.exception("Readiness check failed: %s", exc)
        return JSONResponse({"ok": False, "error": "db"}, status_code=503)
    return JSONResponse({"ok": True})


init_jobs()

