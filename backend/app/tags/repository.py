"""Parameterized SQL access for the global tag catalogue."""

from typing import Any
from uuid import UUID

import psycopg


class DuplicateTagError(Exception):
    """Raised when a normalized tag name already exists."""


class UnknownTagError(Exception):
    """Raised when a profile selection references an absent catalogue tag."""


def search_tags(database_url: str, query: str, limit: int) -> list[dict[str, str]]:
    """Find normalized names with a stable alphabetical order."""
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id, name FROM tags
            WHERE strpos(normalized_name, %s) > 0
            ORDER BY normalized_name, id
            LIMIT %s
            """,
            (query, limit),
        ).fetchall()
    return [_summary(row) for row in rows]


def create_tag(database_url: str, user_id: str, name: str, normalized: str) -> dict[str, str]:
    """Create one globally reusable tag attributed to its member author."""
    try:
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO tags (name, normalized_name, created_by_user_id)
                VALUES (%s, %s, %s) RETURNING id, name
                """,
                (name, normalized, user_id),
            ).fetchone()
    except psycopg.errors.UniqueViolation as error:
        raise DuplicateTagError from error
    return _summary(row)


def replace_profile_tags(database_url: str, user_id: str, tag_ids: list[UUID]) -> None:
    """Replace a member's tag set atomically after checking catalogue membership."""
    with psycopg.connect(database_url) as connection:
        count = connection.execute(
            "SELECT count(*) FROM tags WHERE id = ANY(%s)", (tag_ids,)
        ).fetchone()[0]
        if count != len(tag_ids):
            raise UnknownTagError
        connection.execute("DELETE FROM profile_tags WHERE user_id = %s", (user_id,))
        connection.executemany(
            "INSERT INTO profile_tags (user_id, tag_id) VALUES (%s, %s)",
            [(user_id, tag_id) for tag_id in tag_ids],
        )


def _summary(row: Any) -> dict[str, str]:
    return {"id": str(row[0]), "name": row[1]}
