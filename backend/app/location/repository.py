"""Manual SQL persistence for approximate member locations."""

from typing import Any
from uuid import UUID

import psycopg


class UnknownLocationError(Exception):
    """Raised when a catalogue location is absent."""


def search_locations(database_url: str, query: str, limit: int) -> list[dict[str, Any]]:
    """Search the offline city/district catalogue with stable ordering."""
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id, city_name, district_name, country_code
            FROM location_catalog
            WHERE strpos(normalized_label, %s) > 0
               OR strpos(lower(city_name), %s) > 0
               OR strpos(lower(coalesce(district_name, '')), %s) > 0
            ORDER BY city_name, district_name NULLS FIRST, id
            LIMIT %s
            """,
            (query, query, query, limit),
        ).fetchall()
    return [_suggestion(row) for row in rows]


def catalogue_locations(database_url: str) -> list[tuple[Any, ...]]:
    """Load reduced catalogue centroids used to discard raw GPS coordinates."""
    with psycopg.connect(database_url) as connection:
        return connection.execute(
            """
            SELECT id, city_name, district_name, country_code,
                   centroid_latitude, centroid_longitude
            FROM location_catalog ORDER BY id
            """
        ).fetchall()


def save_location(database_url: str, user_id: str, catalog_id: UUID, source: str) -> dict[str, Any]:
    """Persist only the chosen catalogue centroid, never raw browser GPS."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT id, city_name, district_name, centroid_latitude, centroid_longitude
            FROM location_catalog WHERE id = %s
            """,
            (catalog_id,),
        ).fetchone()
        if row is None:
            raise UnknownLocationError
        saved = connection.execute(
            """
            INSERT INTO user_locations (
                user_id, catalog_location_id, source, reduced_latitude, reduced_longitude
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                catalog_location_id = EXCLUDED.catalog_location_id,
                source = EXCLUDED.source,
                reduced_latitude = EXCLUDED.reduced_latitude,
                reduced_longitude = EXCLUDED.reduced_longitude,
                updated_at = CURRENT_TIMESTAMP
            RETURNING updated_at
            """,
            (user_id, row[0], source, row[3], row[4]),
        ).fetchone()
    return {
        "catalog_location_id": str(row[0]),
        "city": row[1],
        "district": row[2],
        "source": source,
        "updated_at": saved[0].isoformat(),
    }


def delete_location(database_url: str, user_id: str) -> None:
    """Remove the member location without changing consent history."""
    with psycopg.connect(database_url) as connection:
        connection.execute("DELETE FROM user_locations WHERE user_id = %s", (user_id,))


def _suggestion(row: tuple[Any, ...]) -> dict[str, Any]:
    district = row[2]
    label = f"{row[1]} — {district}" if district else row[1]
    return {
        "id": str(row[0]),
        "city": row[1],
        "district": district,
        "country_code": row[3],
        "label": label,
    }
