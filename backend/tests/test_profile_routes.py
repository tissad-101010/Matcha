"""HTTP contract tests for private onboarding profile endpoints."""

from flask.testing import FlaskClient


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_profile_requires_authentication(client: FlaskClient) -> None:
    assert client.get("/api/v1/me/profile").status_code == 401


def test_profile_update_requires_csrf_and_returns_fresh_profile(
    client: FlaskClient, monkeypatch
) -> None:
    authenticate(client)
    updated: list[dict[str, str]] = []
    monkeypatch.setattr(
        "app.routes.profile.update_profile",
        lambda _url, _user, changes: updated.append(changes),
    )
    monkeypatch.setattr(
        "app.routes.profile.private_profile",
        lambda *_args: {"profile_complete": False, "missing_profile_fields": ["tags"]},
    )

    assert client.patch("/api/v1/me/profile", json={"bio": "Bonjour"}).status_code == 403
    response = client.patch(
        "/api/v1/me/profile",
        json={"bio": "Bonjour"},
        headers={"X-CSRF-Token": "csrf-test"},
    )

    assert response.status_code == 200
    assert updated == [{"bio": "Bonjour"}]
    assert response.get_json()["data"]["missing_profile_fields"] == ["tags"]
