"""Exercise reciprocal likes concurrently against the real PostgreSQL schema."""

from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import psycopg

from app.config import build_config
from app.interactions.repository import upsert_like_and_match


def _create_member(connection, user_id: UUID, suffix: str, tag_id: UUID, location_id: UUID) -> None:  # type: ignore[no-untyped-def]
    connection.execute(
        """INSERT INTO accounts
           (id, email, username, password_hash, status, email_verified_at)
           VALUES (%s, %s, %s, %s, 'active', CURRENT_TIMESTAMP)""",
        (user_id, f"concurrency-{suffix}@example.test", f"concurrency_{suffix}", "x" * 20),
    )
    connection.execute(
        """INSERT INTO profiles (user_id, first_name, last_name, birth_date, gender, bio)
           VALUES (%s, 'Test', 'Concurrency', DATE '1990-01-01', 'non_binary',
                   'Temporary concurrency profile')""",
        (user_id,),
    )
    connection.execute(
        """INSERT INTO consent_events (user_id, purpose, policy_version, granted)
           VALUES (%s, 'matching_preferences', 'concurrency-check', true)""",
        (user_id,),
    )
    connection.execute(
        "INSERT INTO profile_tags (user_id, tag_id) VALUES (%s, %s)", (user_id, tag_id)
    )
    connection.execute(
        """INSERT INTO user_locations
           (user_id, catalog_location_id, source, reduced_latitude, reduced_longitude)
           SELECT %s, id, 'manual', centroid_latitude, centroid_longitude
           FROM location_catalog WHERE id = %s""",
        (user_id, location_id),
    )
    connection.execute("INSERT INTO profile_stats (user_id) VALUES (%s)", (user_id,))
    connection.execute(
        """INSERT INTO photos
           (user_id, object_key, mime_type, byte_size, width, height, position, is_main)
           VALUES (%s, %s, 'image/webp', 1, 1, 1, 1, true)""",
        (user_id, f"concurrency/{user_id}.webp"),
    )


def assert_single_relationship(database_url: str, first_id: UUID, second_id: UUID) -> None:
    """Fail unless concurrent operations produced exactly one coherent relationship."""
    low_id, high_id = sorted((first_id, second_id))
    with psycopg.connect(database_url) as connection:
        likes = connection.execute(
            """SELECT count(*) FROM likes WHERE is_active AND
               ((source_user_id = %s AND target_user_id = %s)
                OR (source_user_id = %s AND target_user_id = %s))""",
            (first_id, second_id, second_id, first_id),
        ).fetchone()[0]
        matches = connection.execute(
            """SELECT count(*) FROM matches WHERE user_low_id = %s
               AND user_high_id = %s AND status = 'active'""",
            (low_id, high_id),
        ).fetchone()[0]
        conversations = connection.execute(
            """SELECT count(*) FROM conversations AS conversation
               JOIN matches AS match ON match.id = conversation.match_id
               WHERE match.user_low_id = %s AND match.user_high_id = %s""",
            (low_id, high_id),
        ).fetchone()[0]
    if likes != 2 or matches != 1 or conversations != 1:
        raise RuntimeError(
            f"Invalid concurrent result: likes={likes}, matches={matches}, "
            f"conversations={conversations}"
        )


def main() -> None:
    database_url = str(build_config()["DATABASE_URL"])
    first_id, second_id = uuid4(), uuid4()
    with psycopg.connect(database_url) as connection:
        tag_id = connection.execute("SELECT id FROM tags ORDER BY id LIMIT 1").fetchone()[0]
        location_id = connection.execute(
            "SELECT id FROM location_catalog ORDER BY id LIMIT 1"
        ).fetchone()[0]
        _create_member(connection, first_id, first_id.hex[:12], tag_id, location_id)
        _create_member(connection, second_id, second_id.hex[:12], tag_id, location_id)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = (
                executor.submit(
                    upsert_like_and_match, database_url, str(first_id), str(second_id)
                ),
                executor.submit(
                    upsert_like_and_match, database_url, str(second_id), str(first_id)
                ),
            )
            results = [future.result(timeout=10) for future in futures]
        assert_single_relationship(database_url, first_id, second_id)
        print({"status": "ok", "results": results})
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute("DELETE FROM accounts WHERE id IN (%s, %s)", (first_id, second_id))


if __name__ == "__main__":
    main()
