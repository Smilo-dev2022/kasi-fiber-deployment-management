import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI()

# CORS allowlist
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router.router)
app.include_router(cac_router.router)
app.include_router(pons_geo_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)
app.include_router(photos_upload_router.router)

init_jobs()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    # If needed, extend with DB ping
    return {"ready": True}

