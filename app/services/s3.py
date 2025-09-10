import os
from functools import lru_cache
from typing import Optional

import boto3


class Settings:
    S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "fiber-photos")
    S3_ACCESS_KEY: Optional[str] = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = os.getenv("S3_SECRET_KEY")


settings = Settings()


@lru_cache(maxsize=1)
def get_client():
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )


def get_object_bytes(key: str) -> bytes:
    s3 = get_client()
    obj = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return obj["Body"].read()


def put_bytes(key: str, content_type: str, data: bytes) -> str:
    s3 = get_client()
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{key}".replace("http://", "https://")


def get_presigned_put_url(key: str, content_type: str, expires_seconds: int = 300) -> str:
    s3 = get_client()
    return s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_seconds,
    )

