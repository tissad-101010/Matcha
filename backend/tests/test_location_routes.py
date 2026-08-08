"""HTTP contract tests for approximate location endpoints."""

from flask.testing import FlaskClient


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_catalogue_search_requires_authentication(client: FlaskClient, monkeypatch) -> None:
    assert client.get("/api/v1/locations").status_code == 401
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.location.search_locations",
        lambda _url, query, limit: [{"id": "1", "label": f"{query}:{limit}"}],
    )
    response = client.get("/api/v1/locations?query=paris&limit=5")
    assert response.status_code == 200
    assert response.get_json()["meta"]["count"] == 1


def test_manual_location_is_csrf_protected(client: FlaskClient) -> None:
    authenticate(client)
    response = client.put(
        "/api/v1/me/location/manual",
        json={"catalog_location_id": "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"},
    )
    assert response.status_code == 403


def test_gps_requires_its_own_active_consent(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr("app.routes.location.location_consent_active", lambda *_args: False)
    response = client.put(
        "/api/v1/me/location/gps",
        json={"latitude": 48.8566, "longitude": 2.3522},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "consent_required"


def test_gps_consent_is_independent_and_withdrawable(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    decisions: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "app.routes.profile.record_location_consent",
        lambda _url, _user, version, granted: decisions.append((version, granted)),
    )
    grant = client.put(
        "/api/v1/me/consents/location",
        json={"confirmed": True, "policy_version": "2026-08"},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    withdraw = client.delete("/api/v1/me/consents/location", headers={"X-CSRF-Token": "csrf-test"})
    assert grant.status_code == withdraw.status_code == 204
    assert decisions == [("2026-08", True), ("2026-08", False)]
