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


def test_suggestions_return_documented_envelope(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.discovery.suggestions",
        lambda *_args: {"data": [{"id": "candidate"}], "meta": {"next_cursor": None}},
    )
    response = client.get("/api/v1/discovery/suggestions")
    assert response.status_code == 200
    assert response.get_json()["data"][0]["id"] == "candidate"
