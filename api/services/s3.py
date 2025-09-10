import boto3
from botocore.client import Config
from datetime import timedelta
from ..settings import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def create_bucket_if_not_exists():
    s3 = get_s3_client()
    buckets = s3.list_buckets().get("Buckets", [])
    if not any(b["Name"] == settings.s3_bucket for b in buckets):
        s3.create_bucket(Bucket=settings.s3_bucket)


def get_signed_put_url(key: str, content_type: str) -> str:
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=int(timedelta(minutes=10).total_seconds()),
    )

