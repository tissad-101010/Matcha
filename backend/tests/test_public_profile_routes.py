"""HTTP privacy and authorization contract for detailed public profiles."""

from flask.testing import FlaskClient

TARGET_ID = "00000000-0000-4000-8000-000000000010"


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0


def test_public_profile_requires_authentication(client: FlaskClient) -> None:
    assert client.get(f"/api/v1/profiles/{TARGET_ID}").status_code == 401


def test_public_profile_hides_private_fields(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    public = {
        "id": TARGET_ID,
        "username": "demo010",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "age": 30,
        "location": {"city": "Paris", "district": None},
        "presence": {"online": True, "last_seen_at": None},
        "viewer_state": {"liked_by_me": False, "likes_me": True, "matched": False},
    }
    monkeypatch.setattr("app.routes.public_profiles.get_public_profile", lambda *_args: public)
    payload = client.get(f"/api/v1/profiles/{TARGET_ID}").get_json()["data"]
    assert payload["username"] == "demo010"
    assert payload["viewer_state"]["likes_me"] is True
    assert {"email", "birth_date", "password_hash", "latitude", "longitude"}.isdisjoint(payload)


def test_inaccessible_profile_returns_not_found(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr("app.routes.public_profiles.get_public_profile", lambda *_args: None)
    response = client.get(f"/api/v1/profiles/{TARGET_ID}")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
