"""Benchmark discovery pagination against the mandatory demonstration dataset."""

from math import ceil
from time import perf_counter

import psycopg

from app.config import build_config
from app.discovery.service import suggestions
from app.discovery.validation import DiscoveryQuery

MINIMUM_PROFILE_COUNT = 500
PAGE_SIZE = 50
MAX_PAGE_SECONDS = 0.5


def main() -> int:
    """Require 500 profiles, stable unique pages, and a bounded warm-cache p95."""
    database_url = str(build_config()["DATABASE_URL"])
    with psycopg.connect(database_url) as connection:
        profile_count, user_id = connection.execute(
            """
            SELECT (SELECT count(*) FROM profiles), id
            FROM accounts
            WHERE username = 'demo000'
            """
        ).fetchone()
    if profile_count < MINIMUM_PROFILE_COUNT:
        raise RuntimeError(
            f"Benchmark impossible : {profile_count} profils, minimum {MINIMUM_PROFILE_COUNT}."
        )

    suggestions(database_url, str(user_id), DiscoveryQuery(limit=PAGE_SIZE))
    cursor: str | None = "0"
    identifiers: set[str] = set()
    durations: list[float] = []
    while cursor is not None:
        started_at = perf_counter()
        result = suggestions(
            database_url, str(user_id), DiscoveryQuery(offset=int(cursor), limit=PAGE_SIZE)
        )
        durations.append(perf_counter() - started_at)
        page_ids = [profile["id"] for profile in result["data"]]
        if len(page_ids) > PAGE_SIZE or identifiers.intersection(page_ids):
            raise RuntimeError(
                "La pagination de découverte contient un doublon ou dépasse la limite."
            )
        identifiers.update(page_ids)
        cursor = result["meta"]["next_cursor"]

    p95_seconds = percentile(durations, 0.95)
    if p95_seconds > MAX_PAGE_SECONDS:
        raise RuntimeError(
            f"Découverte trop lente : p95 {p95_seconds * 1000:.1f} ms, "
            f"maximum {MAX_PAGE_SECONDS * 1000:.0f} ms."
        )
    print(
        f"Découverte validée sur {profile_count} profils : {len(identifiers)} suggestions, "
        f"{len(durations)} pages, p95 {p95_seconds * 1000:.1f} ms."
    )
    return 0


def percentile(values: list[float], ratio: float) -> float:
    """Return the nearest-rank percentile, including for a single page."""
    ordered = sorted(values)
    return ordered[max(0, ceil(len(ordered) * ratio) - 1)]


if __name__ == "__main__":
    raise SystemExit(main())
