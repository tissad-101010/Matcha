"""Personal history routes validate access and pagination."""

from flask.testing import FlaskClient


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0


def test_histories_require_authentication(client: FlaskClient) -> None:
    assert client.get("/api/v1/me/visitors").status_code == 401
    assert client.get("/api/v1/me/likes-received").status_code == 401


def test_histories_return_block_safe_repository_results(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr("app.routes.history.visitors", lambda *_args: [{"visited_at": "now"}])
    monkeypatch.setattr("app.routes.history.likes_received", lambda *_args: [{"liked_at": "now"}])
    visits = client.get("/api/v1/me/visitors?period=90&limit=30")
    likes = client.get("/api/v1/me/likes-received?limit=30")
    assert visits.get_json()["meta"] == {"count": 1, "limit": 30}
    assert likes.get_json()["meta"] == {"count": 1, "limit": 30}


def test_history_pagination_and_period_are_validated(client: FlaskClient) -> None:
    authenticate(client)
    assert client.get("/api/v1/me/visitors?period=365").status_code == 422
    assert client.get("/api/v1/me/visitors?before=bad").status_code == 422
    assert client.get("/api/v1/me/likes-received?limit=0").status_code == 422
