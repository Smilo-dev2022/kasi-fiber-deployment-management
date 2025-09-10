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
    # Security controls
    MAX_FILE_SIZE_BYTES: Optional[int] = (
        int(os.getenv("MAX_FILE_SIZE_BYTES")) if os.getenv("MAX_FILE_SIZE_BYTES") else None
    )
    ALLOWED_CONTENT_TYPES: Optional[list[str]] = (
        [t.strip() for t in os.getenv("ALLOWED_CONTENT_TYPES", "").split(",") if t.strip()]
        if os.getenv("ALLOWED_CONTENT_TYPES")
        else None
    )


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
    # Prefer HEAD to enforce size/type constraints before downloading
    head = s3.head_object(Bucket=settings.S3_BUCKET, Key=key)
    content_length: int = int(head.get("ContentLength", 0))
    content_type: str | None = head.get("ContentType")
    if settings.MAX_FILE_SIZE_BYTES is not None and content_length > settings.MAX_FILE_SIZE_BYTES:
        raise ValueError("Object exceeds MAX_FILE_SIZE_BYTES")
    if settings.ALLOWED_CONTENT_TYPES is not None and content_type is not None:
        if content_type not in settings.ALLOWED_CONTENT_TYPES:
            raise ValueError("Disallowed content type")
    obj = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return obj["Body"].read()


def put_bytes(key: str, content_type: str, data: bytes) -> str:
    s3 = get_client()
    # Enforce outgoing content-type and size as well
    if settings.MAX_FILE_SIZE_BYTES is not None and len(data) > settings.MAX_FILE_SIZE_BYTES:
        raise ValueError("Payload exceeds MAX_FILE_SIZE_BYTES")
    if settings.ALLOWED_CONTENT_TYPES is not None and content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise ValueError("Disallowed content type")
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{key}".replace("http://", "https://")


def ensure_bucket_and_lifecycle(prefix_rules: dict[str, dict] | None = None) -> None:
    """Ensure the target bucket exists and optionally apply lifecycle rules per prefix.

    prefix_rules format example:
        {
          "temp/": {"Expiration": {"Days": 7}},
          "reports/": {"NoncurrentVersionExpiration": {"NoncurrentDays": 365}}
        }
    """
    s3 = get_client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET)
    except Exception:
        s3.create_bucket(
            Bucket=settings.S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": settings.S3_REGION}
            if settings.S3_REGION != "us-east-1"
            else {}
        )
    if prefix_rules:
        rules = []
        idx = 1
        for prefix, rule in prefix_rules.items():
            rules.append({
                "ID": f"rule-{idx}",
                "Filter": {"Prefix": prefix},
                "Status": "Enabled",
                **rule,
            })
            idx += 1
        s3.put_bucket_lifecycle_configuration(
            Bucket=settings.S3_BUCKET,
            LifecycleConfiguration={"Rules": rules},
        )

