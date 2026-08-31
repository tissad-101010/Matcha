"""Authorized SQL persistence for the notification center."""

from typing import Any
from uuid import UUID

import psycopg


def list_for_recipient(
    database_url: str, user_id: str, before: UUID | None, limit: int
) -> list[dict[str, Any]]:
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """SELECT notification.id, notification.type, notification.actor_user_id,
                      actor.username, profile.first_name, notification.match_id,
                      notification.conversation_id, notification.message_id,
                      notification.visit_id, notification.read_at, notification.created_at
               FROM notifications AS notification
               JOIN accounts AS actor ON actor.id = notification.actor_user_id
               JOIN profiles AS profile ON profile.user_id = actor.id
               WHERE notification.recipient_user_id = %s
                 AND (%s::uuid IS NULL OR (notification.created_at, notification.id) <
                     (SELECT created_at, id FROM notifications
                      WHERE recipient_user_id = %s AND id = %s))
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                     (blocker_user_id = notification.recipient_user_id
                      AND blocked_user_id = notification.actor_user_id)
                     OR (blocker_user_id = notification.actor_user_id
                         AND blocked_user_id = notification.recipient_user_id))
               ORDER BY notification.created_at DESC, notification.id DESC LIMIT %s""",
            (user_id, before, user_id, before, limit),
        ).fetchall()
    return [_serialize(row) for row in rows]


def unread_count(database_url: str, user_id: str) -> int:
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """SELECT COUNT(*)::integer FROM notifications AS notification
               WHERE recipient_user_id = %s AND read_at IS NULL
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                     (blocker_user_id = notification.recipient_user_id
                      AND blocked_user_id = notification.actor_user_id)
                     OR (blocker_user_id = notification.actor_user_id
                         AND blocked_user_id = notification.recipient_user_id))""",
            (user_id,),
        ).fetchone()
    return row[0]


def mark_one_read(database_url: str, user_id: str, notification_id: UUID) -> bool:
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            """UPDATE notifications SET read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
               WHERE id = %s AND recipient_user_id = %s""",
            (notification_id, user_id),
        )
    return result.rowcount > 0


def mark_all_read(database_url: str, user_id: str) -> int:
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            """UPDATE notifications SET read_at = CURRENT_TIMESTAMP
               WHERE recipient_user_id = %s AND read_at IS NULL""",
            (user_id,),
        )
    return result.rowcount


def _serialize(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": str(row[0]),
        "type": row[1],
        "actor": {
            "id": str(row[2]),
            "username": row[3],
            "first_name": row[4],
        },
        "match_id": str(row[5]) if row[5] else None,
        "conversation_id": str(row[6]) if row[6] else None,
        "message_id": str(row[7]) if row[7] else None,
        "visit_id": str(row[8]) if row[8] else None,
        "read_at": row[9].isoformat() if row[9] else None,
        "created_at": row[10].isoformat(),
    }
