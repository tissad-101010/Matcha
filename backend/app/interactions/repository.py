"""Transactional SQL for likes and matches."""

from typing import Literal
from uuid import UUID

import psycopg

LikeRefusal = Literal["not_found", "blocked", "photo_required"]


def upsert_like_and_match(
    database_url: str, source_id: str, target_id: str
) -> dict[str, object] | LikeRefusal:
    """Lock both accounts, activate the like and create at most one match."""
    low_id, high_id = sorted((UUID(source_id), UUID(target_id)))
    with psycopg.connect(database_url) as connection:
        locked = connection.execute(
            """SELECT id FROM accounts WHERE id IN (%s, %s)
               AND status = 'active' ORDER BY id FOR UPDATE""",
            (low_id, high_id),
        ).fetchall()
        if len(locked) != 2:
            return "not_found"
        if connection.execute(
            """
            SELECT EXISTS(SELECT 1 FROM blocks WHERE
                (blocker_user_id = %s AND blocked_user_id = %s)
                OR (blocker_user_id = %s AND blocked_user_id = %s))
            """,
            (source_id, target_id, target_id, source_id),
        ).fetchone()[0]:
            return "blocked"
        if not connection.execute(
            "SELECT EXISTS(SELECT 1 FROM photos WHERE user_id = %s AND is_main)",
            (source_id,),
        ).fetchone()[0]:
            return "photo_required"
        target_exists = connection.execute(
            "SELECT EXISTS(SELECT 1 FROM public_profiles WHERE user_id = %s)", (target_id,)
        ).fetchone()[0]
        if not target_exists:
            return "not_found"

        previous = connection.execute(
            "SELECT is_active FROM likes WHERE source_user_id = %s AND target_user_id = %s",
            (source_id, target_id),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO likes (source_user_id, target_user_id)
            VALUES (%s, %s)
            ON CONFLICT (source_user_id, target_user_id) DO UPDATE SET
                is_active = true, activated_at = CURRENT_TIMESTAMP, deactivated_at = NULL
            """,
            (source_id, target_id),
        )
        if previous is None or not previous[0]:
            connection.execute(
                """INSERT INTO notifications (recipient_user_id, actor_user_id, type)
                   VALUES (%s, %s, 'like_received')""",
                (target_id, source_id),
            )

        reciprocal = connection.execute(
            """SELECT EXISTS(SELECT 1 FROM likes WHERE source_user_id = %s
                              AND target_user_id = %s AND is_active)""",
            (target_id, source_id),
        ).fetchone()[0]
        match_id = None
        created = False
        if reciprocal:
            existing = connection.execute(
                """SELECT id FROM matches WHERE user_low_id = %s AND user_high_id = %s
                   AND status = 'active'""",
                (low_id, high_id),
            ).fetchone()
            if existing:
                match_id = existing[0]
            else:
                match_id = connection.execute(
                    """INSERT INTO matches (user_low_id, user_high_id)
                       VALUES (%s, %s) RETURNING id""",
                    (low_id, high_id),
                ).fetchone()[0]
                conversation_id = connection.execute(
                    "INSERT INTO conversations (match_id) VALUES (%s) RETURNING id", (match_id,)
                ).fetchone()[0]
                connection.executemany(
                    "INSERT INTO conversation_members (conversation_id, user_id) VALUES (%s, %s)",
                    [(conversation_id, source_id), (conversation_id, target_id)],
                )
                connection.executemany(
                    """INSERT INTO notifications (recipient_user_id, actor_user_id, type, match_id)
                       VALUES (%s, %s, 'match_created', %s)""",
                    [(source_id, target_id, match_id), (target_id, source_id, match_id)],
                )
                created = True
        connection.execute("SELECT recompute_popularity(%s)", (target_id,))
        if match_id:
            connection.execute("SELECT recompute_popularity(%s)", (source_id,))
    return {
        "liked": True,
        "matched": match_id is not None,
        "match_created": created,
        "match_id": str(match_id) if match_id else None,
    }


def deactivate_pair(database_url: str, source_id: str, target_id: str) -> dict[str, object] | None:
    """End a relationship and clear both directions so two new likes are required."""
    low_id, high_id = sorted((UUID(source_id), UUID(target_id)))
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "SELECT id FROM accounts WHERE id IN (%s, %s) ORDER BY id FOR UPDATE", (low_id, high_id)
        ).fetchall()
        active = connection.execute(
            """SELECT EXISTS(SELECT 1 FROM likes WHERE source_user_id = %s
                              AND target_user_id = %s AND is_active)""",
            (source_id, target_id),
        ).fetchone()[0]
        if not active:
            return None
        connection.execute(
            """UPDATE likes SET is_active = false, deactivated_at = CURRENT_TIMESTAMP
               WHERE ((source_user_id = %s AND target_user_id = %s)
                  OR (source_user_id = %s AND target_user_id = %s)) AND is_active""",
            (source_id, target_id, target_id, source_id),
        )
        match = connection.execute(
            """UPDATE matches SET status = 'ended_unlike', ended_at = CURRENT_TIMESTAMP,
                      ended_by_user_id = %s
               WHERE user_low_id = %s AND user_high_id = %s AND status = 'active'
               RETURNING id""",
            (source_id, low_id, high_id),
        ).fetchone()
        if match:
            connection.execute(
                """UPDATE conversations SET can_send = false,
                          closed_at = CURRENT_TIMESTAMP WHERE match_id = %s""",
                (match[0],),
            )
            connection.execute(
                """INSERT INTO notifications (recipient_user_id, actor_user_id, type, match_id)
                   VALUES (%s, %s, 'match_ended', %s)""",
                (target_id, source_id, match[0]),
            )
        connection.execute("SELECT recompute_popularity(%s)", (source_id,))
        connection.execute("SELECT recompute_popularity(%s)", (target_id,))
    return {"liked": False, "matched": False, "match_id": None}
