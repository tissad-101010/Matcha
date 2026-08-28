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


def test_preferences_require_active_consent(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr("app.routes.profile.matching_consent_active", lambda *_args: False)

    response = client.put(
        "/api/v1/me/preferences",
        json={"desired_genders": ["woman"]},
        headers={"X-CSRF-Token": "csrf-test"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "consent_required"


def test_withdrawing_consent_is_separate_and_atomic(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    decisions: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "app.routes.profile.record_matching_consent",
        lambda _url, _user, version, granted: decisions.append((version, granted)),
    )

    grant = client.put(
        "/api/v1/me/consents/preferences",
        json={"confirmed": True, "policy_version": "2026-08"},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    withdraw = client.delete(
        "/api/v1/me/consents/preferences", headers={"X-CSRF-Token": "csrf-test"}
    )

    assert grant.status_code == withdraw.status_code == 204
    assert decisions == [("2026-08", True), ("2026-08", False)]


def test_consents_expose_the_current_policy_version(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.profile.private_profile",
        lambda *_args: {"consents": []},
    )

    response = client.get("/api/v1/me/consents")

    assert response.status_code == 200
    assert response.get_json() == {
        "data": [],
        "meta": {"current_policy_version": "2026-08"},
    }
