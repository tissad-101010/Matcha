"""Authorized persistence for conversations and their messages."""

from typing import Any
from uuid import UUID

import psycopg


def list_for_member(database_url: str, user_id: str) -> list[dict[str, Any]]:
    """List visible, non-blocked conversations for one member."""
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """SELECT conversation.id, conversation.match_id, conversation.can_send,
                      conversation.closed_at, other.id, other.username,
                      profile.first_name, profile.last_name,
                      photo.id,
                      latest.id, latest.author_user_id, latest.body, latest.created_at,
                      COUNT(unread.id)::integer,
                      COALESCE(latest.created_at, conversation.created_at) AS updated_at
               FROM conversation_members AS mine
               JOIN conversations AS conversation ON conversation.id = mine.conversation_id
               JOIN matches AS match ON match.id = conversation.match_id
               JOIN accounts AS other ON other.id = CASE
                   WHEN match.user_low_id = %s THEN match.user_high_id ELSE match.user_low_id END
               JOIN profiles AS profile ON profile.user_id = other.id
               LEFT JOIN photos AS photo ON photo.user_id = other.id AND photo.is_main
               LEFT JOIN LATERAL (
                   SELECT message.id, message.author_user_id, message.body, message.created_at
                   FROM messages AS message
                   WHERE message.conversation_id = conversation.id
                   ORDER BY message.created_at DESC, message.id DESC LIMIT 1
               ) AS latest ON true
               LEFT JOIN messages AS unread
                 ON unread.conversation_id = conversation.id
                AND unread.author_user_id <> %s
                AND (mine.last_read_message_id IS NULL OR unread.created_at >
                    (SELECT created_at FROM messages WHERE id = mine.last_read_message_id))
               WHERE mine.user_id = %s AND mine.hidden_at IS NULL
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                    (blocker_user_id = match.user_low_id AND blocked_user_id = match.user_high_id)
                    OR (blocker_user_id = match.user_high_id
                        AND blocked_user_id = match.user_low_id))
               GROUP BY conversation.id, other.id, profile.user_id, photo.id,
                        latest.id, latest.author_user_id, latest.body, latest.created_at
               ORDER BY updated_at DESC, conversation.id DESC""",
            (user_id, user_id, user_id),
        ).fetchall()
    return [_serialize_conversation(row) for row in rows]


def get_for_member(database_url: str, user_id: str, conversation_id: UUID) -> dict[str, Any] | None:
    """Load one authorized conversation using the same public shape as the list."""
    conversations = list_for_member(database_url, user_id)
    return next((item for item in conversations if item["id"] == str(conversation_id)), None)


def list_messages_for_member(
    database_url: str,
    user_id: str,
    conversation_id: UUID,
    before: UUID | None,
    limit: int,
) -> list[dict[str, str]] | None:
    """Return a stable newest-first page, or None when membership is unauthorized."""
    with psycopg.connect(database_url) as connection:
        allowed = connection.execute(
            """SELECT 1 FROM conversation_members AS member
               JOIN conversations AS conversation ON conversation.id = member.conversation_id
               JOIN matches AS match ON match.id = conversation.match_id
               WHERE member.user_id = %s AND conversation.id = %s
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                    (blocker_user_id = match.user_low_id AND blocked_user_id = match.user_high_id)
                    OR (blocker_user_id = match.user_high_id
                        AND blocked_user_id = match.user_low_id))""",
            (user_id, conversation_id),
        ).fetchone()
        if allowed is None:
            return None
        rows = connection.execute(
            """SELECT message.id, message.conversation_id, message.author_user_id,
                      message.body, message.created_at
               FROM messages AS message
               WHERE message.conversation_id = %s
                 AND (%s::uuid IS NULL OR (message.created_at, message.id) <
                     (SELECT created_at, id FROM messages
                      WHERE conversation_id = %s AND id = %s))
               ORDER BY message.created_at DESC, message.id DESC LIMIT %s""",
            (conversation_id, before, conversation_id, before, limit),
        ).fetchall()
    return [_serialize_message(row) for row in rows]


def mark_read_for_member(
    database_url: str, user_id: str, conversation_id: UUID, message_id: UUID
) -> bool:
    """Advance a member's read marker monotonically within their conversation."""
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            """UPDATE conversation_members AS member
               SET last_read_message_id = target.id
               FROM messages AS target
               JOIN conversations AS conversation ON conversation.id = target.conversation_id
               JOIN matches AS match ON match.id = conversation.match_id
               WHERE member.user_id = %s AND member.conversation_id = %s
                 AND target.id = %s AND target.conversation_id = member.conversation_id
                 AND (member.last_read_message_id IS NULL OR
                      (target.created_at, target.id) > (SELECT created_at, id
                       FROM messages WHERE id = member.last_read_message_id))
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                    (blocker_user_id = match.user_low_id AND blocked_user_id = match.user_high_id)
                    OR (blocker_user_id = match.user_high_id
                        AND blocked_user_id = match.user_low_id))""",
            (user_id, conversation_id, message_id),
        )
        if result.rowcount > 0:
            return True
        exists = connection.execute(
            """SELECT 1 FROM conversation_members AS member
               JOIN messages AS message ON message.conversation_id = member.conversation_id
               WHERE member.user_id = %s AND member.conversation_id = %s AND message.id = %s""",
            (user_id, conversation_id, message_id),
        ).fetchone()
    return exists is not None


def insert_message(
    database_url: str,
    user_id: str,
    conversation_id: UUID,
    client_message_id: UUID,
    body: str,
) -> dict[str, str] | None:
    """Persist an idempotent message after locking and authorizing its conversation."""
    with psycopg.connect(database_url) as connection:
        authorized = connection.execute(
            """SELECT conversation.can_send,
                      CASE WHEN match.user_low_id = %s
                           THEN match.user_high_id ELSE match.user_low_id END
               FROM conversations AS conversation
               JOIN conversation_members AS member
                 ON member.conversation_id = conversation.id
               JOIN matches AS match ON match.id = conversation.match_id
               WHERE conversation.id = %s
                 AND member.user_id = %s
                 AND match.ended_at IS NULL
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                    (blocker_user_id = match.user_low_id
                     AND blocked_user_id = match.user_high_id)
                    OR (blocker_user_id = match.user_high_id
                        AND blocked_user_id = match.user_low_id))
               FOR UPDATE OF conversation""",
            (user_id, conversation_id, user_id),
        ).fetchone()
        if authorized is None or not authorized[0]:
            return None

        row = connection.execute(
            """INSERT INTO messages (
                   conversation_id, author_user_id, client_message_id, body
               ) VALUES (%s, %s, %s, %s)
               ON CONFLICT (author_user_id, client_message_id) DO UPDATE
               SET client_message_id = EXCLUDED.client_message_id
               RETURNING id, conversation_id, author_user_id, body, created_at""",
            (conversation_id, user_id, client_message_id, body),
        ).fetchone()
        if row is None or row[1] != conversation_id:
            return None
        notification = connection.execute(
            """INSERT INTO notifications (
                   recipient_user_id, actor_user_id, type, conversation_id, message_id
               ) VALUES (%s, %s, 'message_received', %s, %s)
               ON CONFLICT (message_id) WHERE type = 'message_received' DO UPDATE
               SET message_id = EXCLUDED.message_id
               RETURNING id, created_at""",
            (authorized[1], user_id, conversation_id, row[0]),
        ).fetchone()
        connection.execute(
            """UPDATE conversation_members
               SET hidden_at = NULL
               WHERE conversation_id = %s""",
            (conversation_id,),
        )
    result = {
        "id": str(row[0]),
        "conversation_id": str(row[1]),
        "author_id": str(row[2]),
        "body": row[3],
        "created_at": row[4].isoformat(),
    }
    result["_recipient_id"] = str(authorized[1])
    if notification is not None:
        result["_notification_id"] = str(notification[0])
        result["_notification_created_at"] = notification[1].isoformat()
    return result


def hide_for_member(database_url: str, user_id: str, conversation_id: UUID) -> bool:
    """Hide one conversation for one member without deleting shared history."""
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            """UPDATE conversation_members AS member
               SET hidden_at = CURRENT_TIMESTAMP
               FROM conversations AS conversation
               JOIN matches AS match ON match.id = conversation.match_id
               WHERE member.conversation_id = conversation.id
                 AND member.user_id = %s
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                    (blocker_user_id = match.user_low_id
                     AND blocked_user_id = match.user_high_id)
                    OR (blocker_user_id = match.user_high_id
                        AND blocked_user_id = match.user_low_id))""",
            (conversation_id, user_id),
        )
    return result.rowcount > 0


def _serialize_message(row: tuple[Any, ...]) -> dict[str, str]:
    return {
        "id": str(row[0]),
        "conversation_id": str(row[1]),
        "author_id": str(row[2]),
        "body": row[3],
        "created_at": row[4].isoformat(),
    }


def _serialize_conversation(row: tuple[Any, ...]) -> dict[str, Any]:
    latest = None
    if row[9] is not None:
        latest = {
            "id": str(row[9]),
            "conversation_id": str(row[0]),
            "author_id": str(row[10]),
            "body": row[11],
            "created_at": row[12].isoformat(),
        }
    return {
        "id": str(row[0]),
        "match_id": str(row[1]),
        "other_user": {
            "id": str(row[4]),
            "username": row[5],
            "first_name": row[6],
            "last_name": row[7],
            "main_photo_id": str(row[8]) if row[8] else None,
        },
        "can_send": row[2],
        "read_only_reason": None if row[2] else "unlike",
        "last_message": latest,
        "unread_count": row[13],
        "updated_at": row[14].isoformat(),
    }
