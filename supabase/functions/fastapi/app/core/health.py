from fastapi import APIRouter, Response
from sqlalchemy import text
from app.core.deps import get_db_session
from app.core.redis_client import ping_redis
from app.services.s3 import s3_client, S3_BUCKET


router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz():
    return {"ok": True}


@router.get("/readyz")
def readyz():
    # DB
    try:
        with get_db_session() as db:
            db.execute(text("select 1"))
    except Exception as e:
        return Response(content=f"db not ready: {e}", status_code=503)
    # Redis
    import asyncio
    try:
        ok = asyncio.run(ping_redis())
        if not ok:
            return Response(content="redis not ready", status_code=503)
    except Exception as e:
        return Response(content=f"redis not ready: {e}", status_code=503)
    # S3
    try:
        s3 = s3_client()
        s3.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=1)
    except Exception as e:
        return Response(content=f"s3 not ready: {e}", status_code=503)
    return {"ok": True}


@router.get("/readyz-async")
async def readyz_async():
    # DB
    try:
        with get_db_session() as db:
            db.execute(text("select 1"))
    except Exception as e:
        return Response(content=f"db not ready: {e}", status_code=503)
    # Redis
    try:
        ok = await ping_redis()
        if not ok:
            return Response(content="redis not ready", status_code=503)
    except Exception as e:
        return Response(content=f"redis not ready: {e}", status_code=503)
    # S3
    try:
        s3 = s3_client()
        s3.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=1)
    except Exception as e:
        return Response(content=f"s3 not ready: {e}", status_code=503)
    return {"ok": True}

