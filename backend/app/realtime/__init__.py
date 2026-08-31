"""Authenticated real-time delivery."""

from typing import Any
from uuid import UUID

from flask import current_app, request
from flask_socketio import SocketIO, emit, join_room

from app.auth.session_access import authenticated_user_id
from app.conversations.service import mark_read, send_message
from app.interactions.service import InteractionError


def register_realtime_handlers(socket: SocketIO) -> None:
    """Register session-authenticated Socket.IO lifecycle handlers."""

    @socket.on("connect")
    def connect(_auth: Any = None):  # type: ignore[no-untyped-def]
        user_id = authenticated_user_id()
        if user_id is None:
            return False
        join_room(user_room(user_id))
        return True

    @socket.on("message:send")
    def message_send(payload: Any):  # type: ignore[no-untyped-def]
        user_id = authenticated_user_id()
        if user_id is None:
            return {"error": {"code": "authentication_required"}}
        try:
            if not isinstance(payload, dict):
                raise ValueError
            conversation_id = UUID(str(payload.get("conversation_id", "")))
            client_message_id = UUID(str(payload.get("client_message_id", "")))
            message = send_message(
                str(current_app.config["DATABASE_URL"]),
                user_id,
                conversation_id,
                client_message_id,
                payload.get("body"),
            )
        except (ValueError, AttributeError):
            return {"error": {"code": "validation_error", "message": "Message invalide."}}
        except InteractionError as error:
            return {"error": {"code": error.code, "message": error.message}}
        public = {key: value for key, value in message.items() if not key.startswith("_")}
        emit("message:new", {"message": public}, to=user_room(message["_recipient_id"]))
        emit(
            "message:ack",
            {"client_message_id": str(client_message_id), "message": public},
            to=request.sid,
        )
        emit(
            "notification.created",
            {
                "id": message.get("_notification_id"),
                "type": "message_received",
                "actor_user_id": user_id,
                "conversation_id": str(conversation_id),
                "message_id": public["id"],
                "created_at": message.get("_notification_created_at"),
            },
            to=user_room(message["_recipient_id"]),
        )
        return {"ok": True}

    @socket.on("conversation:read")
    def conversation_read(payload: Any):  # type: ignore[no-untyped-def]
        user_id = authenticated_user_id()
        if user_id is None:
            return {"error": {"code": "authentication_required"}}
        try:
            if not isinstance(payload, dict):
                raise ValueError
            mark_read(
                str(current_app.config["DATABASE_URL"]),
                user_id,
                UUID(str(payload.get("conversation_id", ""))),
                UUID(str(payload.get("message_id", ""))),
            )
        except (ValueError, AttributeError):
            return {"error": {"code": "validation_error"}}
        except InteractionError as error:
            return {"error": {"code": error.code, "message": error.message}}
        return {"ok": True}


def user_room(user_id: str) -> str:
    """Return the private, non-user-controlled room for one account."""
    return f"user:{user_id}"
