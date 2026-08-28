"""Transactional persistence for blocks and reports."""

from typing import Any
from uuid import UUID

import psycopg


def create_block(database_url: str, blocker_id: str, blocked_id: str) -> dict[str, Any] | None:
    """Block a user and atomically neutralize the relationship in both directions."""
    low_id, high_id = sorted((UUID(blocker_id), UUID(blocked_id)))
    with psycopg.connect(database_url) as connection:
        accounts = connection.execute(
            """SELECT id FROM accounts WHERE id IN (%s, %s)
               AND status = 'active' ORDER BY id FOR UPDATE""",
            (low_id, high_id),
        ).fetchall()
        if len(accounts) != 2:
            return None
        row = connection.execute(
            """INSERT INTO blocks (blocker_user_id, blocked_user_id)
               VALUES (%s, %s) ON CONFLICT DO NOTHING
               RETURNING created_at""",
            (blocker_id, blocked_id),
        ).fetchone()
        if row is None:
            row = connection.execute(
                """SELECT created_at FROM blocks
                   WHERE blocker_user_id = %s AND blocked_user_id = %s""",
                (blocker_id, blocked_id),
            ).fetchone()
        connection.execute(
            """UPDATE likes SET is_active = false, deactivated_at = CURRENT_TIMESTAMP
               WHERE ((source_user_id = %s AND target_user_id = %s)
                  OR (source_user_id = %s AND target_user_id = %s)) AND is_active""",
            (blocker_id, blocked_id, blocked_id, blocker_id),
        )
        match = connection.execute(
            """UPDATE matches SET status = 'ended_block', ended_at = CURRENT_TIMESTAMP,
                      ended_by_user_id = %s
               WHERE user_low_id = %s AND user_high_id = %s AND status = 'active'
               RETURNING id""",
            (blocker_id, low_id, high_id),
        ).fetchone()
        if match:
            connection.execute(
                """UPDATE conversations SET can_send = false,
                          closed_at = CURRENT_TIMESTAMP WHERE match_id = %s""",
                (match[0],),
            )
        connection.execute("SELECT recompute_popularity(%s)", (blocker_id,))
        connection.execute("SELECT recompute_popularity(%s)", (blocked_id,))
    return {"user_id": blocked_id, "created_at": row[0].isoformat()}


def remove_block(database_url: str, blocker_id: str, blocked_id: str) -> bool:
    """Remove only the block; previous likes and matches remain inactive."""
    with psycopg.connect(database_url) as connection:
        result = connection.execute(
            "DELETE FROM blocks WHERE blocker_user_id = %s AND blocked_user_id = %s",
            (blocker_id, blocked_id),
        )
    return result.rowcount > 0


def create_report(
    database_url: str,
    reporter_id: str,
    reported_id: str,
    reason: str,
    description: str | None,
) -> dict[str, str] | None:
    """Create an immutable report, reusing an existing report for the same pair and reason."""
    with psycopg.connect(database_url) as connection:
        target = connection.execute(
            "SELECT id FROM accounts WHERE id = %s AND status = 'active'", (reported_id,)
        ).fetchone()
        if target is None:
            return None
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (f"report:{reporter_id}:{reported_id}:{reason}",),
        )
        existing = connection.execute(
            """SELECT id FROM reports WHERE reporter_user_id = %s
               AND reported_user_id = %s AND reason = %s ORDER BY created_at LIMIT 1""",
            (reporter_id, reported_id, reason),
        ).fetchone()
        if existing:
            return {"id": str(existing[0])}
        report_id = connection.execute(
            """INSERT INTO reports (reporter_user_id, reported_user_id, reason, description)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (reporter_id, reported_id, reason, description),
        ).fetchone()[0]
    return {"id": str(report_id)}
