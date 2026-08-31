"""Blocked-user-safe personal visit and like history queries."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import psycopg


def visitors(
    database_url: str,
    user_id: str,
    before: UUID | None,
    limit: int,
    period_days: int | None,
) -> list[dict[str, Any]]:
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """SELECT visit.id, visit.visited_at, public.user_id, public.first_name,
                      public.age, public.city_name, public.district_name,
                      public.popularity_score, public.last_seen_at,
                      photo.id
               FROM visits AS visit
               JOIN public_profiles AS public ON public.user_id = visit.visitor_user_id
               LEFT JOIN photos AS photo ON photo.user_id = public.user_id AND photo.is_main
               WHERE visit.visited_user_id = %s
                 AND (%s::integer IS NULL OR visit.visited_at >=
                      CURRENT_TIMESTAMP - make_interval(days => %s))
                 AND (%s::uuid IS NULL OR (visit.visited_at, visit.id) <
                     (SELECT visited_at, id FROM visits
                      WHERE visited_user_id = %s AND id = %s))
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                     (blocker_user_id = %s AND blocked_user_id = visit.visitor_user_id)
                     OR (blocker_user_id = visit.visitor_user_id AND blocked_user_id = %s))
               ORDER BY visit.visited_at DESC, visit.id DESC LIMIT %s""",
            (
                user_id,
                period_days,
                period_days,
                before,
                user_id,
                before,
                user_id,
                user_id,
                limit,
            ),
        ).fetchall()
        return [
            {"visitor": _card(connection, row[2:]), "visited_at": row[1].isoformat()}
            for row in rows
        ]


def likes_received(
    database_url: str, user_id: str, before: UUID | None, limit: int
) -> list[dict[str, Any]]:
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """SELECT likes.id, likes.activated_at, public.user_id, public.first_name,
                      public.age, public.city_name, public.district_name,
                      public.popularity_score, public.last_seen_at,
                      photo.id
               FROM likes
               JOIN public_profiles AS public ON public.user_id = likes.source_user_id
               LEFT JOIN photos AS photo ON photo.user_id = public.user_id AND photo.is_main
               WHERE likes.target_user_id = %s AND likes.is_active
                 AND (%s::uuid IS NULL OR (likes.activated_at, likes.id) <
                     (SELECT activated_at, id FROM likes
                      WHERE target_user_id = %s AND id = %s))
                 AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                     (blocker_user_id = %s AND blocked_user_id = likes.source_user_id)
                     OR (blocker_user_id = likes.source_user_id AND blocked_user_id = %s))
               ORDER BY likes.activated_at DESC, likes.id DESC LIMIT %s""",
            (user_id, before, user_id, before, user_id, user_id, limit),
        ).fetchall()
        return [
            {"user": _card(connection, row[2:]), "liked_at": row[1].isoformat()} for row in rows
        ]


def _card(connection, row: tuple[Any, ...]) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    tags = connection.execute(
        """SELECT tag.id, tag.name FROM profile_tags
           JOIN tags AS tag ON tag.id = profile_tags.tag_id
           WHERE profile_tags.user_id = %s ORDER BY tag.name""",
        (row[0],),
    ).fetchall()
    return {
        "id": str(row[0]),
        "first_name": row[1],
        "age": row[2],
        "main_photo": ({"id": str(row[7]), "url": f"/api/v1/photos/{row[7]}"} if row[7] else None),
        "tags": [{"id": str(tag[0]), "name": tag[1]} for tag in tags],
        "location": {"city": row[3], "district": row[4]},
        "popularity": row[5],
        "presence": {
            "online": bool(row[6] and row[6] >= datetime.now(UTC) - timedelta(minutes=2)),
            "last_seen_at": row[6].isoformat() if row[6] else None,
        },
    }
