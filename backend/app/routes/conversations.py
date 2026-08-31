"""Authenticated conversation history endpoints."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_csrf
from app.conversations.service import hide_conversation, send_message
from app.interactions.service import InteractionError

conversations_blueprint = Blueprint("conversations", __name__, url_prefix="/api/v1/conversations")


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
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return jsonify({"data": message}), 201


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
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return "", 204


def _message_error(message: str, status: int):  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": "validation_error", "message": message}}), status
