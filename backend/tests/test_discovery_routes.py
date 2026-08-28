"""HTTP contract tests for profile suggestions."""

from flask.testing import FlaskClient


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0


def test_suggestions_require_authentication(client: FlaskClient) -> None:
    assert client.get("/api/v1/discovery/suggestions").status_code == 401


def test_suggestions_validate_pagination(client: FlaskClient) -> None:
    authenticate(client)
    response = client.get("/api/v1/discovery/suggestions?limit=51")
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"


def test_suggestions_validate_filter_ranges(client: FlaskClient) -> None:
    authenticate(client)
    response = client.get("/api/v1/discovery/suggestions?age_min=40&age_max=20")
    assert response.status_code == 422
    assert "age_max" in response.get_json()["error"]["fields"]
    assert client.get("/api/v1/discovery/suggestions?distance_max_km=nan").status_code == 422


def test_suggestions_pass_validated_filters(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    captured = []

    def fake_suggestions(_database_url, _user_id, query):  # type: ignore[no-untyped-def]
        captured.append(query)
        return {"data": [], "meta": {"next_cursor": None, "count": 0}}

    monkeypatch.setattr("app.routes.discovery.suggestions", fake_suggestions)
    response = client.get(
        "/api/v1/discovery/suggestions?sort=distance&age_min=25&popularity_max=80"
        "&distance_max_km=12.5"
    )
    assert response.status_code == 200
    assert captured[0].sort == "distance"
    assert captured[0].age_min == 25
    assert captured[0].distance_max_km == 12.5
    assert captured[0].popularity_max == 80


def test_suggestions_return_documented_envelope(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.discovery.suggestions",
        lambda *_args: {"data": [{"id": "candidate"}], "meta": {"next_cursor": None}},
    )
    response = client.get("/api/v1/discovery/suggestions")
    assert response.status_code == 200
    assert response.get_json()["data"][0]["id"] == "candidate"
