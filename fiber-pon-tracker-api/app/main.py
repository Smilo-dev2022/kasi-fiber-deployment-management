from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, users, pons, photos


app = FastAPI(title="Fiber PON Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ALLOWED_ORIGINS == "*" else settings.CORS_ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pons.router)
app.include_router(photos.router)


@app.get("/health")
def health():
    return {"ok": True}
