"""Manual SQL reads for eligible discovery candidates."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg


@dataclass(frozen=True)
class ViewerContext:
    gender: str
    preferences: tuple[str, ...]
    latitude: float
    longitude: float
    location_id: UUID
    city: str
    district: str | None
    tag_ids: frozenset[UUID]


@dataclass(frozen=True)
class Candidate:
    id: UUID
    first_name: str
    age: int
    gender: str
    preferences: tuple[str, ...]
    latitude: float
    longitude: float
    location_id: UUID
    city: str
    district: str | None
    popularity: int
    last_seen_at: datetime | None
    photo_id: UUID | None
    tags: tuple[dict[str, str], ...]
    tag_ids: frozenset[UUID]


def load_viewer(database_url: str, user_id: str) -> ViewerContext | None:
    """Load only the current member data required to calculate suggestions."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT profile.gender, location.reduced_latitude, location.reduced_longitude,
                   location.catalog_location_id, catalog.city_name, catalog.district_name,
                   ARRAY(SELECT desired_gender FROM user_preferences
                         WHERE user_id = profile.user_id ORDER BY desired_gender),
                   ARRAY(SELECT tag_id FROM profile_tags WHERE user_id = profile.user_id)
            FROM profiles AS profile
            JOIN profile_completeness AS complete ON complete.user_id = profile.user_id
            JOIN user_locations AS location ON location.user_id = profile.user_id
            JOIN location_catalog AS catalog ON catalog.id = location.catalog_location_id
            WHERE profile.user_id = %s AND complete.is_complete
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return ViewerContext(
        row[0],
        tuple(row[6]),
        float(row[1]),
        float(row[2]),
        row[3],
        row[4],
        row[5],
        frozenset(row[7]),
    )


def load_eligible_candidates(database_url: str, user_id: str) -> list[Candidate]:
    """Exclude self, blocked, incomplete, inactive and unconsented profiles in SQL."""
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT profile.user_id, profile.first_name,
                   date_part('year', age(CURRENT_DATE, profile.birth_date))::integer,
                   profile.gender, location.reduced_latitude, location.reduced_longitude,
                   location.catalog_location_id, catalog.city_name, catalog.district_name,
                   stats.popularity_score, coalesce(stats.last_seen_at, account.last_login_at),
                   main_photo.id,
                   ARRAY(SELECT desired_gender FROM user_preferences
                         WHERE user_id = profile.user_id ORDER BY desired_gender),
                   coalesce((SELECT jsonb_agg(jsonb_build_object(
                       'id', tag.id, 'name', tag.name) ORDER BY tag.name)
                       FROM profile_tags JOIN tags AS tag ON tag.id = profile_tags.tag_id
                       WHERE profile_tags.user_id = profile.user_id), '[]'::jsonb),
                   ARRAY(SELECT tag_id FROM profile_tags WHERE user_id = profile.user_id)
            FROM profiles AS profile
            JOIN accounts AS account ON account.id = profile.user_id AND account.status = 'active'
            JOIN profile_completeness AS complete
              ON complete.user_id = profile.user_id AND complete.is_complete
            JOIN current_consents AS consent
              ON consent.user_id = profile.user_id
             AND consent.purpose = 'matching_preferences' AND consent.granted
            JOIN user_locations AS location ON location.user_id = profile.user_id
            JOIN location_catalog AS catalog ON catalog.id = location.catalog_location_id
            JOIN profile_stats AS stats ON stats.user_id = profile.user_id
            LEFT JOIN photos AS main_photo
              ON main_photo.user_id = profile.user_id AND main_photo.is_main
            WHERE profile.user_id <> %s
              AND NOT EXISTS (
                  SELECT 1 FROM blocks
                  WHERE (blocker_user_id = %s AND blocked_user_id = profile.user_id)
                     OR (blocker_user_id = profile.user_id AND blocked_user_id = %s)
              )
            """,
            (user_id, user_id, user_id),
        ).fetchall()
    return [_candidate(row) for row in rows]


def _candidate(row: tuple[Any, ...]) -> Candidate:
    tags = tuple({"id": str(item["id"]), "name": item["name"]} for item in row[13])
    return Candidate(
        row[0],
        row[1],
        row[2],
        row[3],
        tuple(row[12]),
        float(row[4]),
        float(row[5]),
        row[6],
        row[7],
        row[8],
        row[9],
        row[10],
        row[11],
        tags,
        frozenset(row[14]),
    )
