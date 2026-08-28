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
        events: list[dict[str, str]] = []
        if previous is None or not previous[0]:
            notification = connection.execute(
                """INSERT INTO notifications (recipient_user_id, actor_user_id, type)
                   VALUES (%s, %s, 'like_received') RETURNING id, created_at""",
                (target_id, source_id),
            ).fetchone()
            events.append(
                {
                    "recipient_user_id": target_id,
                    "id": str(notification[0]),
                    "type": "like_received",
                    "actor_user_id": source_id,
                    "created_at": notification[1].isoformat(),
                }
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
        "_events": events,
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


def insert_visit(
    database_url: str, visitor_id: str, visited_id: str
) -> tuple[bool, dict[str, str] | None]:
    """Record an authorized human visit and notify at most once per 24 hours."""
    with psycopg.connect(database_url) as connection:
        authorized = connection.execute(
            """SELECT EXISTS(SELECT 1 FROM public_profiles WHERE user_id = %s)
               AND NOT EXISTS(SELECT 1 FROM blocks WHERE
                   (blocker_user_id = %s AND blocked_user_id = %s)
                   OR (blocker_user_id = %s AND blocked_user_id = %s))""",
            (visited_id, visitor_id, visited_id, visited_id, visitor_id),
        ).fetchone()[0]
        if not authorized:
            return False, None
        connection.execute(
            "DELETE FROM visits WHERE visited_at < CURRENT_TIMESTAMP - INTERVAL '90 days'"
        )
        notification_eligible = not connection.execute(
            """SELECT EXISTS(SELECT 1 FROM visits
               WHERE visitor_user_id = %s AND visited_user_id = %s
                 AND notification_sent
                 AND visited_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')""",
            (visitor_id, visited_id),
        ).fetchone()[0]
        visit = connection.execute(
            """INSERT INTO visits (visitor_user_id, visited_user_id, notification_sent)
               VALUES (%s, %s, %s) RETURNING id""",
            (visitor_id, visited_id, notification_eligible),
        ).fetchone()
        if notification_eligible:
            notification = connection.execute(
                """INSERT INTO notifications
                   (recipient_user_id, actor_user_id, type, visit_id)
                   VALUES (%s, %s, 'profile_visited', %s)
                   RETURNING id, created_at""",
                (visited_id, visitor_id, visit[0]),
            ).fetchone()
            event = {
                "id": str(notification[0]),
                "type": "profile_visited",
                "actor_user_id": visitor_id,
                "created_at": notification[1].isoformat(),
            }
        else:
            event = None
        connection.execute("SELECT recompute_popularity(%s)", (visited_id,))
    return True, event
