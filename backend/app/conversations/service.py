"""Conversation history business rules."""

from uuid import UUID

from app.conversations.repository import hide_for_member
from app.interactions.service import InteractionError


def hide_conversation(database_url: str, user_id: str, conversation_id: UUID) -> None:
    """Apply a local hide preference to an authorized conversation member."""
    if not hide_for_member(database_url, user_id, conversation_id):
        raise InteractionError("not_found", "Conversation introuvable.", 404)
