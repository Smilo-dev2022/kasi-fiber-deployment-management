from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Literal
from app.core.deps import get_db, require_roles
from app.models.photo import Photo
from uuid import UUID
from app.services.s3 import put_bytes


router = APIRouter(prefix="/photos", tags=["photos"])


ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/upload", dependencies=[Depends(require_roles("ADMIN", "PM", "SITE", "SMME"))])
async def upload_photo(photo_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Unsupported content type")
    # Read in chunks to enforce size limit
    total = 0
    chunks: list[bytes] = []
    while True:
        data = await file.read(1024 * 1024)
        if not data:
            break
        total += len(data)
        if total > MAX_BYTES:
            raise HTTPException(413, "File too large")
        chunks.append(data)
    blob = b"".join(chunks)
    key = f"photos/{photo_id}.{ 'jpg' if file.content_type in ('image/jpeg','image/jpg') else 'png'}"
    url = put_bytes(key, file.content_type, blob)
    p = db.get(Photo, UUID(photo_id))
    if not p:
        raise HTTPException(404, "Photo not found")
    # Save asset_code as key and rely on register/validate for EXIF rules
    p.asset_code = key
    db.commit()
    return {"ok": True, "s3_key": key, "url": url}

