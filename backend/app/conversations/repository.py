"""Authorized persistence for conversations and their messages."""

from uuid import UUID

import psycopg


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
            """SELECT conversation.can_send
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
            (conversation_id, user_id),
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
        connection.execute(
            """UPDATE conversation_members
               SET hidden_at = NULL
               WHERE conversation_id = %s""",
            (conversation_id,),
        )
    return {
        "id": str(row[0]),
        "conversation_id": str(row[1]),
        "author_id": str(row[2]),
        "body": row[3],
        "created_at": row[4].isoformat(),
    }


def hide_for_member(database_url: str, user_id: str, conversation_id: UUID) -> bool:
    """Hide one conversation for one member without deleting shared history."""
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            """UPDATE conversation_members AS member
               SET hidden_at = CURRENT_TIMESTAMP
               FROM conversations AS conversation
               JOIN matches AS match ON match.id = conversation.match_id
               WHERE member.conversation_id = conversation.id
                 AND member.conversation_id = %s
                 AND member.user_id = %s
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                    (blocker_user_id = match.user_low_id
                     AND blocked_user_id = match.user_high_id)
                    OR (blocker_user_id = match.user_high_id
                        AND blocked_user_id = match.user_low_id))""",
            (conversation_id, user_id),
        )
    return result.rowcount > 0
