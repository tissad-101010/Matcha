"""Conversation history business rules."""

from uuid import UUID

from app.conversations.repository import hide_for_member, insert_message
from app.interactions.service import InteractionError


def hide_conversation(database_url: str, user_id: str, conversation_id: UUID) -> None:
    """Apply a local hide preference to an authorized conversation member."""
    if not hide_for_member(database_url, user_id, conversation_id):
        raise InteractionError("not_found", "Conversation introuvable.", 404)


def send_message(
    database_url: str,
    user_id: str,
    conversation_id: UUID,
    client_message_id: UUID,
    body: object,
) -> dict[str, str]:
    """Validate and persist one idempotent message for an active match."""
    if client_message_id.version != 4:
        raise InteractionError("validation_error", "Identifiant de message invalide.", 422)
    if not isinstance(body, str):
        raise InteractionError("validation_error", "Message invalide.", 422)
    normalized = body.strip()
    if not normalized or len(normalized) > 2000:
        raise InteractionError("validation_error", "Message invalide.", 422)
    message = insert_message(database_url, user_id, conversation_id, client_message_id, normalized)
    if message is None:
        raise InteractionError("not_found", "Conversation introuvable.", 404)
    return message
