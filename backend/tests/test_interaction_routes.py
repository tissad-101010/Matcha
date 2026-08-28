"""HTTP contract for likes and unlikes."""

from flask.testing import FlaskClient

TARGET_ID = "00000000-0000-4000-8000-000000000010"


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_like_requires_authentication_and_csrf(client: FlaskClient) -> None:
    assert client.post(f"/api/v1/profiles/{TARGET_ID}/like").status_code == 401
    authenticate(client)
    response = client.post(f"/api/v1/profiles/{TARGET_ID}/like")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_like_returns_atomic_relationship_state(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    expected = {
        "liked": True,
        "matched": True,
        "match_created": True,
        "match_id": "00000000-0000-4000-8000-000000000099",
    }
    monkeypatch.setattr("app.routes.interactions.like_profile", lambda *_args: expected)
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/like", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"data": expected}


def test_unlike_returns_disconnected_state(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    expected = {"liked": False, "matched": False, "match_id": None}
    monkeypatch.setattr("app.routes.interactions.unlike_profile", lambda *_args: expected)
    response = client.delete(
        f"/api/v1/profiles/{TARGET_ID}/like", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"data": expected}
