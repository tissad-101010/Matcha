"""Authenticated real-time delivery."""

from typing import Any

from flask_socketio import SocketIO, join_room

from app.auth.session_access import authenticated_user_id


def register_realtime_handlers(socket: SocketIO) -> None:
    """Register session-authenticated Socket.IO lifecycle handlers."""

    @socket.on("connect")
    def connect(_auth: Any = None):  # type: ignore[no-untyped-def]
        user_id = authenticated_user_id()
        if user_id is None:
            return False
        join_room(user_room(user_id))
        return True


def user_room(user_id: str) -> str:
    """Return the private, non-user-controlled room for one account."""
    return f"user:{user_id}"
