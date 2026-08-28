"""Authenticated conversation history endpoints."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify

from app.auth.session_access import authenticated_user_id, require_csrf
from app.conversations.service import hide_conversation
from app.interactions.service import InteractionError

conversations_blueprint = Blueprint(
    "conversations", __name__, url_prefix="/api/v1/conversations"
)


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
