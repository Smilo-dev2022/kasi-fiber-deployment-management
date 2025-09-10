from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .settings import settings
from .db.session import get_db
from .auth import router as auth_router
from .routers.__mount import mount_all
from .deps import get_current_user
from .schemas.user import UserOut


app = FastAPI(title="FiberTime PON Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.cors_allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
mount_all(app)


@app.get("/health", tags=["System"])
def health_check():
    return {"ok": True}


@app.get("/users/me", response_model=UserOut, tags=["Users"])
def read_users_me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return current_user

