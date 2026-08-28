"""Authorized persistence for conversation history preferences."""

from uuid import UUID

import psycopg


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
