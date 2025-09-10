from fastapi import FastAPI
from . import pons, tasks, photos, cac, stringing, stock, smmes, invoices, reports, upload


def mount_all(app: FastAPI) -> None:
    app.include_router(pons.router)
    app.include_router(tasks.router)
    app.include_router(photos.router)
    app.include_router(cac.router)
    app.include_router(stringing.router)
    app.include_router(stock.router)
    app.include_router(smmes.router)
    app.include_router(invoices.router)
    app.include_router(reports.router)
    app.include_router(upload.router)

