from fastapi import APIRouter, Depends
from ..deps import get_current_user
from ..services.s3 import get_signed_put_url, create_bucket_if_not_exists


router = APIRouter(tags=["Upload"])


@router.post("/upload")
def upload_url(filename: str, content_type: str, user=Depends(get_current_user)):
    create_bucket_if_not_exists()
    return {"url": get_signed_put_url(filename, content_type)}

