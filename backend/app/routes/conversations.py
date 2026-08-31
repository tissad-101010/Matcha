"""Authenticated conversation history endpoints."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.conversations.service import (
    conversation,
    conversations,
    hide_conversation,
    mark_read,
    messages,
    send_message,
)
from app.interactions.service import InteractionError

conversations_blueprint = Blueprint("conversations", __name__, url_prefix="/api/v1/conversations")


@conversations_blueprint.get("")
@require_auth
def list_conversations():  # type: ignore[no-untyped-def]
    data = conversations(str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "")
    return jsonify({"data": data, "meta": {"count": len(data)}})


@conversations_blueprint.get("/<uuid:conversation_id>")
@require_auth
def get_conversation(conversation_id: UUID):  # type: ignore[no-untyped-def]
    try:
        data = conversation(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            conversation_id,
        )
    except InteractionError as error:
        return _interaction_error(error)
    return jsonify({"data": data})


@conversations_blueprint.get("/<uuid:conversation_id>/messages")
@require_auth
def list_messages(conversation_id: UUID):  # type: ignore[no-untyped-def]
    try:
        limit = int(request.args.get("limit", "20"))
        if limit < 1 or limit > 50:
            raise ValueError
        before_raw = request.args.get("before")
        before = UUID(before_raw) if before_raw else None
    except (ValueError, AttributeError):
        return _message_error("Pagination invalide.", 422)
    try:
        data = messages(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            conversation_id,
            before,
            limit,
        )
    except InteractionError as error:
        return _interaction_error(error)
    return jsonify({"data": data, "meta": {"count": len(data), "limit": limit}})


@conversations_blueprint.post("/<uuid:conversation_id>/messages")
@require_csrf
def create_message(conversation_id: UUID):  # type: ignore[no-untyped-def]
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _message_error("Requête JSON invalide.", 422)
    try:
        client_message_id = UUID(str(payload.get("client_message_id", "")))
    except (ValueError, AttributeError):
        return _message_error("Identifiant de message invalide.", 422)
    try:
        message = send_message(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            conversation_id,
            client_message_id,
            payload.get("body"),
        )
    except InteractionError as error:
        return _interaction_error(error)
    return jsonify({"data": _public_message(message)}), 201


@conversations_blueprint.post("/<uuid:conversation_id>/read")
@require_csrf
def read_conversation(conversation_id: UUID):  # type: ignore[no-untyped-def]
    payload = request.get_json(silent=True)
    try:
        message_id = UUID(str(payload.get("message_id", ""))) if isinstance(payload, dict) else None
    except (ValueError, AttributeError):
        message_id = None
    if message_id is None:
        return _message_error("Identifiant de message invalide.", 422)
    try:
        mark_read(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            conversation_id,
            message_id,
        )
    except InteractionError as error:
        return _interaction_error(error)
    return "", 204


@conversations_blueprint.post("/<uuid:conversation_id>/hide")
@require_csrf
def hide_conversation_for_current_user(conversation_id: UUID):  # type: ignore[no-untyped-def]
    try:
        hide_conversation(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            conversation_id,
        )
    except InteractionError as error:
        return _interaction_error(error)
    return "", 204


def _message_error(message: str, status: int):  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": "validation_error", "message": message}}), status


def _interaction_error(error: InteractionError):  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": error.code, "message": error.message}}), error.status


def _public_message(message: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in message.items() if not key.startswith("_")}
