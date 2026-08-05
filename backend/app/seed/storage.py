"""Store deterministic seed avatars in the private S3-compatible bucket."""

import boto3

from app.seed.avatars import avatar_bytes
from app.seed.identifiers import stable_id


def s3_client(config: dict[str, object]):
    """Create the S3-compatible client from backend configuration."""
    return boto3.client(
        "s3",
        endpoint_url=str(config["S3_ENDPOINT_URL"]),
        region_name=str(config["S3_REGION"]),
        aws_access_key_id=str(config["S3_ACCESS_KEY"]),
        aws_secret_access_key=str(config["S3_SECRET_KEY"]),
    )


def upload_avatars(client, profiles: list[dict[str, object]]) -> list[tuple[object, ...]]:
    """Upload one private synthetic avatar and return its SQL metadata rows."""
    photo_rows = []
    for profile in profiles:
        index = int(profile["index"])
        user_id = profile["id"]
        photo_id = stable_id("photo", index)
        object_key = f"profiles/{user_id}/{photo_id}.webp"
        content = avatar_bytes(index)
        client.put_object(
            Bucket="profile-photos",
            Key=object_key,
            Body=content,
            ContentType="image/webp",
        )
        photo_rows.append((photo_id, user_id, object_key, len(content), 256, 256, 1, True))
    return photo_rows
