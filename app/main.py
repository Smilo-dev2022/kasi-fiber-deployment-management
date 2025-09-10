from fastapi import FastAPI

from app.routers import tasks as tasks_router
from app.routers import cac as cac_router
from app.routers import pons_geofence as pons_geo_router
from app.routers import photos_validate as photos_val_router
from app.routers import assets as assets_router
from app.routers import reports as reports_router
from app.routers import reports_ops as reports_ops_router
from app.routers import rate_cards as rate_router
from app.routers import pay_sheets as pays_router
from app.routers import photos_upload_hook as photos_upload_router
from app.scheduler import init_jobs
from app.routers import devices as devices_router
from app.routers import incidents as incidents_router
from app.routers import optical as optical_router
from app.routers import nms_webhook as nms_router
from app.routers import pons_detail as pons_detail_router


app = FastAPI()

app.include_router(tasks_router.router)
app.include_router(cac_router.router)
app.include_router(pons_geo_router.router)
app.include_router(pons_detail_router.router)
app.include_router(photos_val_router.router)
app.include_router(assets_router.router)
app.include_router(reports_router.router)
app.include_router(reports_ops_router.router)
app.include_router(rate_router.router)
app.include_router(pays_router.router)
app.include_router(photos_upload_router.router)
app.include_router(devices_router.router)
app.include_router(incidents_router.router)
app.include_router(optical_router.router)
app.include_router(nms_router.router)

init_jobs()

