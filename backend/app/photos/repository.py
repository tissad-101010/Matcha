"""Transactional SQL metadata operations for profile photos."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg


class PhotoLimitError(Exception):
    """Raised when a sixth mandatory profile photo is attempted."""


class PhotoNotFoundError(Exception):
    """Raised when a photo is absent or not owned by the current member."""


@dataclass(frozen=True)
class StoredPhoto:
    id: UUID
    object_key: str
    position: int
    is_main: bool
    width: int
    height: int


def insert_photo(
    database_url: str,
    photo_id: UUID,
    user_id: str,
    object_key: str,
    byte_size: int,
    width: int,
    height: int,
) -> StoredPhoto:
    """Serialize concurrent additions by locking the owning profile row."""
    with psycopg.connect(database_url) as connection:
        connection.execute("SELECT user_id FROM profiles WHERE user_id = %s FOR UPDATE", (user_id,))
        current = connection.execute(
            "SELECT count(*), coalesce(max(position), 0) FROM photos WHERE user_id = %s",
            (user_id,),
        ).fetchone()
        if current[0] >= 5:
            raise PhotoLimitError
        position = int(current[1]) + 1
        is_main = current[0] == 0
        connection.execute(
            """
            INSERT INTO photos (
                id, user_id, object_key, mime_type, byte_size,
                width, height, position, is_main
            ) VALUES (%s, %s, %s, 'image/webp', %s, %s, %s, %s, %s)
            """,
            (photo_id, user_id, object_key, byte_size, width, height, position, is_main),
        )
    return StoredPhoto(photo_id, object_key, position, is_main, width, height)


def list_photos(database_url: str, user_id: str) -> list[StoredPhoto]:
    """List only metadata owned by the current member."""
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id, object_key, position, is_main, width, height
            FROM photos WHERE user_id = %s ORDER BY position
            """,
            (user_id,),
        ).fetchall()
    return [_stored(row) for row in rows]


def find_accessible_photo(database_url: str, photo_id: UUID, viewer_id: str) -> StoredPhoto:
    """Authorize own media or a compatible, complete and unblocked public profile."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT photo.id, photo.object_key, photo.position, photo.is_main,
                   photo.width, photo.height
            FROM photos AS photo
            JOIN accounts AS owner ON owner.id = photo.user_id
            JOIN profiles AS target ON target.user_id = photo.user_id
            WHERE photo.id = %s AND (
                photo.user_id = %s OR (
                    owner.status = 'active'
                    AND EXISTS (SELECT 1 FROM profile_completeness
                                WHERE user_id = photo.user_id AND is_complete)
                    AND EXISTS (SELECT 1 FROM profile_completeness
                                WHERE user_id = %s AND is_complete)
                    AND EXISTS (SELECT 1 FROM current_consents WHERE user_id = photo.user_id
                                AND purpose = 'matching_preferences' AND granted)
                    AND EXISTS (SELECT 1 FROM current_consents WHERE user_id = %s
                                AND purpose = 'matching_preferences' AND granted)
                    AND NOT EXISTS (SELECT 1 FROM blocks WHERE
                        (blocker_user_id = %s AND blocked_user_id = photo.user_id)
                        OR (blocker_user_id = photo.user_id AND blocked_user_id = %s))
                    AND EXISTS (SELECT 1 FROM profiles AS viewer WHERE viewer.user_id = %s
                        AND (NOT EXISTS (SELECT 1 FROM user_preferences WHERE user_id = %s)
                             OR target.gender IN (SELECT desired_gender FROM user_preferences
                                                  WHERE user_id = %s))
                        AND (NOT EXISTS (SELECT 1 FROM user_preferences
                                        WHERE user_id = photo.user_id)
                             OR viewer.gender IN (SELECT desired_gender FROM user_preferences
                                                  WHERE user_id = photo.user_id)))
                )
            )
            """,
            (
                photo_id,
                viewer_id,
                viewer_id,
                viewer_id,
                viewer_id,
                viewer_id,
                viewer_id,
                viewer_id,
                viewer_id,
            ),
        ).fetchone()
    if row is None:
        raise PhotoNotFoundError
    return _stored(row)


def update_photo(
    database_url: str, user_id: str, photo_id: UUID, position: int | None, is_main: bool
) -> list[StoredPhoto]:
    """Reorder or select a main photo while preserving deferred SQL invariants."""
    with psycopg.connect(database_url) as connection:
        connection.execute("SELECT user_id FROM profiles WHERE user_id = %s FOR UPDATE", (user_id,))
        owned = connection.execute(
            "SELECT position FROM photos WHERE id = %s AND user_id = %s", (photo_id, user_id)
        ).fetchone()
        if owned is None:
            raise PhotoNotFoundError
        if position is not None and position != owned[0]:
            _move_photo(connection, user_id, photo_id, int(owned[0]), position)
        if is_main:
            connection.execute("UPDATE photos SET is_main = false WHERE user_id = %s", (user_id,))
            connection.execute("UPDATE photos SET is_main = true WHERE id = %s", (photo_id,))
    return list_photos(database_url, user_id)


def remove_photo(database_url: str, user_id: str, photo_id: UUID) -> tuple[str, UUID]:
    """Delete metadata, promote a replacement and enqueue durable object cleanup."""
    with psycopg.connect(database_url) as connection:
        connection.execute("SELECT user_id FROM profiles WHERE user_id = %s FOR UPDATE", (user_id,))
        row = connection.execute(
            "SELECT object_key, position, is_main FROM photos WHERE id = %s AND user_id = %s",
            (photo_id, user_id),
        ).fetchone()
        if row is None:
            raise PhotoNotFoundError
        connection.execute("DELETE FROM photos WHERE id = %s", (photo_id,))
        connection.execute(
            "UPDATE photos SET position = position - 1 WHERE user_id = %s AND position > %s",
            (user_id, row[1]),
        )
        if row[2]:
            connection.execute(
                """
                UPDATE photos SET is_main = true
                WHERE id = (SELECT id FROM photos WHERE user_id = %s ORDER BY position LIMIT 1)
                """,
                (user_id,),
            )
        job_id = connection.execute(
            "INSERT INTO deletion_jobs (user_id, object_keys) VALUES (%s, %s) RETURNING id",
            (user_id, [row[0]]),
        ).fetchone()[0]
    return str(row[0]), job_id


def complete_deletion_job(database_url: str, job_id: UUID) -> None:
    """Remove the durable retry marker after successful object deletion."""
    with psycopg.connect(database_url) as connection:
        connection.execute("DELETE FROM deletion_jobs WHERE id = %s", (job_id,))


def _move_photo(connection: Any, user_id: str, photo_id: UUID, old: int, new: int) -> None:
    count = connection.execute(
        "SELECT count(*) FROM photos WHERE user_id = %s", (user_id,)
    ).fetchone()[0]
    if not 1 <= new <= count:
        raise ValueError("position")
    connection.execute(
        """
        UPDATE photos SET position = CASE
            WHEN id = %s THEN %s
            WHEN %s < %s AND position >= %s AND position < %s THEN position + 1
            WHEN %s > %s AND position > %s AND position <= %s THEN position - 1
            ELSE position END
        WHERE user_id = %s
        """,
        (photo_id, new, new, old, new, old, new, old, old, new, user_id),
    )


def _stored(row: tuple[Any, ...]) -> StoredPhoto:
    return StoredPhoto(row[0], row[1], row[2], row[3], row[4], row[5])
