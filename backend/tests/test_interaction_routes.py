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


def test_like_emits_only_persisted_notification_without_leaking_room_data(
    client: FlaskClient, monkeypatch
) -> None:
    authenticate(client)
    event = {
        "recipient_user_id": TARGET_ID,
        "id": "00000000-0000-4000-8000-000000000099",
        "type": "like_received",
        "actor_user_id": "e8d7a810-4cb8-47ec-b359-70fdc5288a9a",
        "created_at": "2026-08-28T09:20:00+00:00",
    }
    monkeypatch.setattr(
        "app.routes.interactions.like_profile",
        lambda *_args: {
            "liked": True,
            "matched": False,
            "match_created": False,
            "match_id": None,
            "_events": [event],
        },
    )
    emissions = []
    monkeypatch.setattr(
        "app.routes.interactions.socketio.emit",
        lambda name, payload, **kwargs: emissions.append((name, payload, kwargs)),
    )
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/like", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 200
    assert "_events" not in response.get_json()["data"]
    assert "recipient_user_id" not in emissions[0][1]
    assert emissions[0][0] == "notification.created"
    assert emissions[0][2] == {"to": f"user:{TARGET_ID}"}


def test_idempotent_like_without_new_notification_emits_nothing(
    client: FlaskClient, monkeypatch
) -> None:
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.interactions.like_profile",
        lambda *_args: {
            "liked": True,
            "matched": False,
            "match_created": False,
            "match_id": None,
            "_events": [],
        },
    )
    emissions = []
    monkeypatch.setattr(
        "app.routes.interactions.socketio.emit",
        lambda *args, **kwargs: emissions.append((args, kwargs)),
    )
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/like", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 200
    assert emissions == []


def test_unlike_returns_disconnected_state(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    expected = {"liked": False, "matched": False, "match_id": None}
    monkeypatch.setattr("app.routes.interactions.unlike_profile", lambda *_args: expected)
    response = client.delete(
        f"/api/v1/profiles/{TARGET_ID}/like", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"data": expected}


def test_block_is_csrf_protected_and_returns_summary(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    expected = {"user_id": TARGET_ID, "created_at": "2026-08-28T08:00:00+00:00"}
    monkeypatch.setattr("app.routes.interactions.block_profile", lambda *_args: expected)
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/block", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"data": expected}


def test_unblock_returns_no_content(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    monkeypatch.setattr("app.routes.interactions.unblock_profile", lambda *_args: None)
    response = client.delete(
        f"/api/v1/profiles/{TARGET_ID}/block", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 204


def test_report_validates_and_normalizes_input(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    captured = {}

    def report(*args):  # type: ignore[no-untyped-def]
        captured["args"] = args
        return {"id": "00000000-0000-4000-8000-000000000099"}

    monkeypatch.setattr("app.routes.interactions.report_profile", report)
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/reports",
        json={"reason": "fake_profile", "description": "  détails   utiles  "},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 201
    assert captured["args"][-2:] == ("fake_profile", "détails utiles")


def test_report_rejects_unknown_reason(client: FlaskClient) -> None:
    authenticate(client)
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/reports",
        json={"reason": "revenge"},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 422
    assert "reason" in response.get_json()["error"]["fields"]


def test_explicit_visit_is_recorded_once_by_the_client(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    calls = []
    monkeypatch.setattr(
        "app.routes.interactions.record_profile_visit",
        lambda *args: calls.append(args),
    )
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/visit", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 204
    assert len(calls) == 1


def test_visit_notification_is_emitted_to_the_recipient_room(
    client: FlaskClient, monkeypatch
) -> None:
    authenticate(client)
    notification = {
        "id": "00000000-0000-4000-8000-000000000099",
        "type": "profile_visited",
        "actor_user_id": "e8d7a810-4cb8-47ec-b359-70fdc5288a9a",
        "created_at": "2026-08-28T09:00:00+00:00",
    }
    emissions = []
    monkeypatch.setattr(
        "app.routes.interactions.record_profile_visit", lambda *_args: notification
    )
    monkeypatch.setattr(
        "app.routes.interactions.socketio.emit",
        lambda event, payload, **kwargs: emissions.append((event, payload, kwargs)),
    )
    response = client.post(
        f"/api/v1/profiles/{TARGET_ID}/visit", headers={"X-CSRF-Token": "csrf-test"}
    )
    assert response.status_code == 204
    assert emissions == [
        ("notification.created", notification, {"to": f"user:{TARGET_ID}"})
    ]
