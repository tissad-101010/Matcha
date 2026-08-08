"""Coordination tests for SQL and private object storage consistency."""

from uuid import UUID

import pytest

from app.photos.image_processing import ProcessedImage
from app.photos.repository import PhotoLimitError
from app.photos.service import add_profile_photo


def test_failed_metadata_insert_compensates_uploaded_object(monkeypatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        "app.photos.service.process_image", lambda _content: ProcessedImage(b"webp", 10, 10)
    )
    monkeypatch.setattr("app.photos.service.photo_client", lambda _config: object())
    monkeypatch.setattr("app.photos.service.put_photo", lambda *_args: events.append("put"))
    monkeypatch.setattr("app.photos.service.delete_photo", lambda *_args: events.append("delete"))
    monkeypatch.setattr(
        "app.photos.service.insert_photo",
        lambda *_args: (_ for _ in ()).throw(PhotoLimitError()),
    )

    with pytest.raises(PhotoLimitError):
        add_profile_photo({"DATABASE_URL": "database"}, str(UUID(int=1)), b"input")
    assert events == ["put", "delete"]
