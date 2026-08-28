"""Coordinate image neutralization, SQL metadata and private object storage."""

from typing import Any
from uuid import UUID, uuid4

from app.photos.image_processing import process_image
from app.photos.repository import (
    StoredPhoto,
    complete_deletion_job,
    insert_photo,
    remove_photo,
)
from app.photos.storage import delete_photo, photo_client, put_photo


def add_profile_photo(
    config: dict[str, object], user_id: str, untrusted_content: bytes
) -> dict[str, Any]:
    """Upload sanitized bytes and compensate if relational insertion fails."""
    image = process_image(untrusted_content)
    photo_id = uuid4()
    object_key = f"profiles/{user_id}/{photo_id}.webp"
    client = photo_client(config)
    put_photo(client, object_key, image.content)
    try:
        photo = insert_photo(
            str(config["DATABASE_URL"]),
            photo_id,
            user_id,
            object_key,
            len(image.content),
            image.width,
            image.height,
        )
    except Exception:
        delete_photo(client, object_key)
        raise
    return photo_summary(photo)


def delete_profile_photo(config: dict[str, object], user_id: str, photo_id: UUID) -> None:
    """Commit metadata first, then consume its durable deletion job."""
    database_url = str(config["DATABASE_URL"])
    object_key, job_id = remove_photo(database_url, user_id, photo_id)
    delete_photo(photo_client(config), object_key)
    complete_deletion_job(database_url, job_id)


def photo_summary(photo: StoredPhoto) -> dict[str, Any]:
    """Serialize safe metadata without leaking its MinIO object key."""
    return {
        "id": str(photo.id),
        "url": f"/api/v1/photos/{photo.id}",
        "position": photo.position,
        "is_main": photo.is_main,
        "width": photo.width,
        "height": photo.height,
    }
