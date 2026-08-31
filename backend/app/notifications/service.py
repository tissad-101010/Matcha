"""Notification center business rules."""

from uuid import UUID

from app.interactions.service import InteractionError
from app.notifications.repository import mark_all_read, mark_one_read


def read_one(database_url: str, user_id: str, notification_id: UUID) -> None:
    if not mark_one_read(database_url, user_id, notification_id):
        raise InteractionError("not_found", "Notification introuvable.", 404)


def read_all(database_url: str, user_id: str) -> int:
    return mark_all_read(database_url, user_id)
