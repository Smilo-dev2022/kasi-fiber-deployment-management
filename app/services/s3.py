import os
from functools import lru_cache
from typing import Optional

import boto3
from botocore.client import Config


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
        config=Config(s3={"addressing_style": "path"}),
    )


def get_object_bytes(key: str) -> bytes:
    s3 = get_client()
    obj = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return obj["Body"].read()


def put_bytes(key: str, content_type: str, data: bytes) -> str:
    s3 = get_client()
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{key}".replace("http://", "https://")


def create_presigned_post(key: str, content_type: str, max_mb: int = 10):
    s3 = get_client()
    conditions = [["content-length-range", 1, max_mb * 1024 * 1024], {"Content-Type": content_type}]
    fields = {"Content-Type": content_type}
    resp = s3.generate_presigned_post(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=600,
    )
    return resp

