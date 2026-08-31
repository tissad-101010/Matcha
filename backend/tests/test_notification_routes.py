"""Notification center HTTP authorization and response contracts."""

from flask.testing import FlaskClient

NOTIFICATION_ID = "00000000-0000-4000-8000-000000000060"


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_notification_center_requires_authentication(client: FlaskClient) -> None:
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications/unread-count").status_code == 401


def test_notification_center_lists_and_counts(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.notifications.list_for_recipient", lambda *_args: [{"id": "one"}]
    )
    monkeypatch.setattr("app.routes.notifications.unread_count", lambda *_args: 3)
    listed = client.get("/api/v1/notifications?limit=40")
    counted = client.get("/api/v1/notifications/unread-count")
    assert listed.get_json()["meta"] == {"count": 1, "limit": 40}
    assert counted.get_json()["data"]["unread_count"] == 3


def test_notification_pagination_is_validated(client: FlaskClient) -> None:
    authenticate(client)
    assert client.get("/api/v1/notifications?limit=101").status_code == 422
    assert client.get("/api/v1/notifications?before=bad").status_code == 422


def test_notification_reads_require_csrf(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    path = f"/api/v1/notifications/{NOTIFICATION_ID}/read"
    assert client.post(path).status_code == 403
    calls = []
    monkeypatch.setattr("app.routes.notifications.read_one", lambda *args: calls.append(args))
    response = client.post(path, headers={"X-CSRF-Token": "csrf-test"})
    assert response.status_code == 204
    assert str(calls[0][-1]) == NOTIFICATION_ID


def test_mark_all_returns_updated_count(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr("app.routes.notifications.read_all", lambda *_args: 4)
    response = client.post("/api/v1/notifications/read-all", headers={"X-CSRF-Token": "csrf-test"})
    assert response.status_code == 200
    assert response.get_json()["data"]["updated_count"] == 4
