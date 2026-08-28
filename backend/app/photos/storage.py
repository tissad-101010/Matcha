"""Private S3-compatible storage operations for profile photos."""

from io import BytesIO
from typing import Any

import boto3

BUCKET = "profile-photos"


def photo_client(config: dict[str, object]):
    """Create a provider-independent S3-compatible client from configuration."""
    return boto3.client(
        "s3",
        endpoint_url=str(config["S3_ENDPOINT_URL"]),
        region_name=str(config["S3_REGION"]),
        aws_access_key_id=str(config["S3_ACCESS_KEY"]),
        aws_secret_access_key=str(config["S3_SECRET_KEY"]),
    )


def put_photo(client: Any, object_key: str, content: bytes) -> None:
    """Store only the server-generated WebP under a non-public key."""
    client.put_object(
        Bucket=BUCKET,
        Key=object_key,
        Body=content,
        ContentType="image/webp",
        CacheControl="private, no-store",
    )


def read_photo(client: Any, object_key: str) -> BytesIO:
    """Read a private object after the route has authorized its metadata."""
    response = client.get_object(Bucket=BUCKET, Key=object_key)
    return BytesIO(response["Body"].read())


def delete_photo(client: Any, object_key: str) -> None:
    """Idempotently delete a private object."""
    client.delete_object(Bucket=BUCKET, Key=object_key)
