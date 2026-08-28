"""Socket.IO authentication uses the existing server-side session."""

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import socketio


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
