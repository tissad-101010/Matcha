"""Socket.IO authentication uses the existing server-side session."""

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import socketio

CONVERSATION_ID = "00000000-0000-4000-8000-000000000050"


def test_anonymous_socket_is_rejected(app: Flask) -> None:
    socket_client = socketio.test_client(app)
    assert not socket_client.is_connected()


def test_authenticated_socket_joins_private_delivery_channel(
    app: Flask, client: FlaskClient, monkeypatch
) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
    joined = []
    monkeypatch.setattr("app.realtime.join_room", lambda room: joined.append(room))
    socket_client = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected()
    assert joined == ["user:e8d7a810-4cb8-47ec-b359-70fdc5288a9a"]
    socket_client.disconnect()


def test_authenticated_socket_persists_and_acknowledges_message(
    app: Flask, client: FlaskClient, monkeypatch
) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
    monkeypatch.setattr(
        "app.realtime.send_message",
        lambda *_args: {
            "id": "message-id",
            "conversation_id": CONVERSATION_ID,
            "author_id": "e8d7a810-4cb8-47ec-b359-70fdc5288a9a",
            "body": "Bonjour",
            "created_at": "2026-08-31T12:00:00+00:00",
            "_recipient_id": "00000000-0000-4000-8000-000000000099",
            "_notification_id": "notification-id",
            "_notification_created_at": "2026-08-31T12:00:00+00:00",
        },
    )
    socket_client = socketio.test_client(app, flask_test_client=client)
    result = socket_client.emit(
        "message:send",
        {
            "conversation_id": CONVERSATION_ID,
            "client_message_id": "e3fa8774-5162-4b31-a8d6-aef88210c059",
            "body": "Bonjour",
        },
        callback=True,
    )
    assert result == {"ok": True}
    events = socket_client.get_received()
    assert [event["name"] for event in events] == ["message:ack"]
    assert events[0]["args"][0]["message"]["body"] == "Bonjour"
    socket_client.disconnect()


def test_socket_rejects_malformed_message(app: Flask, client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
    socket_client = socketio.test_client(app, flask_test_client=client)
    result = socket_client.emit("message:send", {"conversation_id": "bad"}, callback=True)
    assert result["error"]["code"] == "validation_error"
    socket_client.disconnect()
