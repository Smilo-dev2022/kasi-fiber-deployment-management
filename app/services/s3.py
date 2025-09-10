import os
import boto3


def get_client():
    endpoint = os.getenv("S3_ENDPOINT")
    region = os.getenv("S3_REGION", "us-east-1")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    params = {
        "service_name": "s3",
        "region_name": region,
    }
    if endpoint:
        params["endpoint_url"] = endpoint
    if access_key and secret_key:
        params["aws_access_key_id"] = access_key
        params["aws_secret_access_key"] = secret_key
    return boto3.client(**params)


def get_object_bytes(key: str) -> bytes:
    s3 = get_client()
    bucket = os.getenv("S3_BUCKET")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()


def put_bytes(key: str, content_type: str, data: bytes) -> str:
    s3 = get_client()
    bucket = os.getenv("S3_BUCKET")
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    endpoint = os.getenv("S3_ENDPOINT", "")
    url = f"{endpoint}/{bucket}/{key}" if endpoint else key
    return url.replace("http://", "https://")

