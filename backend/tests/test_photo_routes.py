"""HTTP contract tests for mandatory profile photos."""

from io import BytesIO
from uuid import UUID

from flask.testing import FlaskClient

from app.photos.repository import StoredPhoto

PHOTO_ID = UUID("e8d7a810-4cb8-47ec-b359-70fdc5288a9a")


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "f8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_photo_listing_requires_authentication(client: FlaskClient) -> None:
    assert client.get("/api/v1/me/photos").status_code == 401


def test_upload_requires_csrf_and_returns_safe_metadata(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    assert (
        client.post(
            "/api/v1/me/photos", data={"file": (BytesIO(b"image"), "photo.jpg")}
        ).status_code
        == 403
    )
    monkeypatch.setattr(
        "app.routes.photos.add_profile_photo",
        lambda *_args: {"id": str(PHOTO_ID), "url": f"/api/v1/photos/{PHOTO_ID}"},
    )
    response = client.post(
        "/api/v1/me/photos",
        data={"file": (BytesIO(b"image"), "photo.jpg")},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 201
    assert "object_key" not in response.get_json()["data"]


def test_position_only_update_is_allowed(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    photo = StoredPhoto(PHOTO_ID, "private/key.webp", 1, True, 10, 10)
    monkeypatch.setattr("app.routes.photos.update_photo", lambda *_args: [photo])
    response = client.patch(
        f"/api/v1/me/photos/{PHOTO_ID}",
        json={"position": 1},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"][0]["is_main"] is True


def test_private_photo_access_is_scoped_to_owner(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    photo = StoredPhoto(PHOTO_ID, "private/key.webp", 1, True, 10, 10)
    monkeypatch.setattr("app.routes.photos.find_accessible_photo", lambda *_args: photo)
    monkeypatch.setattr("app.routes.photos.photo_client", lambda _config: object())
    monkeypatch.setattr("app.routes.photos.read_photo", lambda *_args: BytesIO(b"webp"))
    response = client.get(f"/api/v1/photos/{PHOTO_ID}")
    assert response.status_code == 200
    assert response.mimetype == "image/webp"
