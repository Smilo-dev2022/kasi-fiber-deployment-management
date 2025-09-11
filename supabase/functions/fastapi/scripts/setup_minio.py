import os
from minio import Minio
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter


def main():
    endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000").replace("http://", "").replace("https://", "")
    access_key = os.getenv("S3_ACCESS_KEY", "minio")
    secret_key = os.getenv("S3_SECRET_KEY", "minio12345")
    bucket = os.getenv("S3_BUCKET", "fiber-photos")

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=endpoint.startswith("https"))

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    # Add per-tenant prefixes lifecycle to expire tmp objects after 30d
    rules = [
        Rule(
            rule_id="tmp-expire",
            status="Enabled",
            expiration=Expiration(days=30),
            filter=Filter(prefix="tmp/")
        )
    ]
    lc = LifecycleConfig(rules=rules)
    client.set_bucket_lifecycle(bucket, lc)
    print(f"Configured bucket {bucket} with lifecycle rules")


if __name__ == "__main__":
    main()

