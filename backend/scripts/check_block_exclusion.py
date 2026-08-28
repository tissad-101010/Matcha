"""Verify bidirectional block exclusion against real discovery data."""

import psycopg

from app.config import build_config
from app.discovery.repository import load_eligible_candidates


def assert_excluded(database_url: str, viewer_id: str, candidate_id: str) -> None:
    """Fail if a blocked candidate remains eligible for discovery or search."""
    visible_ids = {
        str(candidate.id)
        for candidate in load_eligible_candidates(database_url, viewer_id)
    }
    if candidate_id in visible_ids:
        raise RuntimeError(f"Blocked profile {candidate_id} remains eligible for {viewer_id}")


def main() -> None:
    database_url = str(build_config()["DATABASE_URL"])
    with psycopg.connect(database_url) as connection:
        viewer_ids = [
            str(row[0])
            for row in connection.execute(
                "SELECT user_id FROM public_profiles ORDER BY username LIMIT 50"
            )
        ]
    pair = None
    for viewer_id in viewer_ids:
        candidates = load_eligible_candidates(database_url, viewer_id)
        if candidates:
            pair = viewer_id, str(candidates[0].id)
            break
    if pair is None:
        raise RuntimeError("No eligible profile pair is available for the block check")
    viewer_id, candidate_id = pair
    try:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                "INSERT INTO blocks (blocker_user_id, blocked_user_id) VALUES (%s, %s)",
                (viewer_id, candidate_id),
            )
        assert_excluded(database_url, viewer_id, candidate_id)
        with psycopg.connect(database_url) as connection:
            connection.execute(
                "DELETE FROM blocks WHERE blocker_user_id = %s AND blocked_user_id = %s",
                (viewer_id, candidate_id),
            )
            connection.execute(
                "INSERT INTO blocks (blocker_user_id, blocked_user_id) VALUES (%s, %s)",
                (candidate_id, viewer_id),
            )
        assert_excluded(database_url, viewer_id, candidate_id)
        print({"status": "ok", "viewer_id": viewer_id, "candidate_id": candidate_id})
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                """DELETE FROM blocks
                   WHERE (blocker_user_id = %s AND blocked_user_id = %s)
                      OR (blocker_user_id = %s AND blocked_user_id = %s)""",
                (viewer_id, candidate_id, candidate_id, viewer_id),
            )


if __name__ == "__main__":
    main()
