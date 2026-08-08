"""Small SQL repository for the private profile aggregate."""

from typing import Any

import psycopg
from psycopg import sql


def get_private_profile(database_url: str, user_id: str) -> dict[str, Any] | None:
    """Load private onboarding data with short, independently auditable queries."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT account.id, account.username, account.email, account.pending_email,
                   profile.first_name, profile.last_name, profile.birth_date,
                   profile.gender, profile.bio, account.created_at, profile.updated_at
            FROM accounts AS account JOIN profiles AS profile ON profile.user_id = account.id
            WHERE account.id = %s AND account.status = 'active'
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        preferences = connection.execute(
            """
            SELECT desired_gender FROM user_preferences
            WHERE user_id = %s ORDER BY desired_gender
            """,
            (user_id,),
        ).fetchall()
        tags = connection.execute(
            """
            SELECT tag.id, tag.name FROM profile_tags
            JOIN tags AS tag ON tag.id = profile_tags.tag_id
            WHERE profile_tags.user_id = %s ORDER BY tag.name
            """,
            (user_id,),
        ).fetchall()
        photos = connection.execute(
            """
            SELECT id, mime_type, byte_size, width, height, position, is_main
            FROM photos WHERE user_id = %s ORDER BY position
            """,
            (user_id,),
        ).fetchall()
        location = connection.execute(
            """
            SELECT catalog.id, catalog.city_name, catalog.district_name, location.source,
                   location.updated_at
            FROM user_locations AS location
            JOIN location_catalog AS catalog ON catalog.id = location.catalog_location_id
            WHERE location.user_id = %s
            """,
            (user_id,),
        ).fetchone()
        consents = connection.execute(
            """
            SELECT DISTINCT ON (purpose) purpose, granted, policy_version, occurred_at
            FROM consent_events WHERE user_id = %s
            ORDER BY purpose, occurred_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

    return _serialize(row, preferences, tags, photos, location, consents)


def update_profile(database_url: str, user_id: str, changes: dict[str, Any]) -> None:
    """Update only allowlisted columns supplied by the validated transfer model."""
    assignments = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(field)) for field in changes
    )
    values = [*changes.values(), user_id]
    with psycopg.connect(database_url) as connection:
        connection.execute(
            sql.SQL("UPDATE profiles SET {} WHERE user_id = %s").format(assignments), values
        )


def matching_consent_active(database_url: str, user_id: str) -> bool:
    """Return only the latest recorded decision for sensitive preferences."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT granted FROM consent_events
            WHERE user_id = %s AND purpose = 'matching_preferences'
            ORDER BY occurred_at DESC, id DESC LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    return bool(row and row[0])


def location_consent_active(database_url: str, user_id: str) -> bool:
    """Return the latest explicit GPS decision independently from preferences."""
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT granted FROM consent_events
            WHERE user_id = %s AND purpose = 'gps_location'
            ORDER BY occurred_at DESC, id DESC LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    return bool(row and row[0])


def replace_preferences(database_url: str, user_id: str, genders: list[str]) -> None:
    """Replace the desired-gender set atomically after consent validation."""
    with psycopg.connect(database_url) as connection:
        connection.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))
        connection.executemany(
            "INSERT INTO user_preferences (user_id, desired_gender) VALUES (%s, %s)",
            [(user_id, gender) for gender in genders],
        )


def record_matching_consent(
    database_url: str, user_id: str, policy_version: str, granted: bool
) -> None:
    """Append an auditable decision and erase preferences immediately on withdrawal."""
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO consent_events (user_id, purpose, policy_version, granted)
            VALUES (%s, 'matching_preferences', %s, %s)
            """,
            (user_id, policy_version, granted),
        )
        if not granted:
            connection.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))


def record_location_consent(
    database_url: str, user_id: str, policy_version: str, granted: bool
) -> None:
    """Append the GPS decision and erase GPS-derived data on withdrawal."""
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO consent_events (user_id, purpose, policy_version, granted)
            VALUES (%s, 'gps_location', %s, %s)
            """,
            (user_id, policy_version, granted),
        )
        if not granted:
            connection.execute(
                "DELETE FROM user_locations WHERE user_id = %s AND source = 'gps_reduced'",
                (user_id,),
            )


def _serialize(row, preferences, tags, photos, location, consents):  # type: ignore[no-untyped-def]
    keys = (
        "id",
        "username",
        "email",
        "pending_email",
        "first_name",
        "last_name",
        "birth_date",
        "gender",
        "bio",
        "created_at",
        "updated_at",
    )
    result = dict(zip(keys, row, strict=True))
    result["id"] = str(result["id"])
    result["birth_date"] = result["birth_date"].isoformat()
    result["created_at"] = result["created_at"].isoformat()
    result["updated_at"] = result["updated_at"].isoformat()
    result["desired_genders"] = [item[0] for item in preferences]
    result["tags"] = [{"id": str(item[0]), "name": item[1]} for item in tags]
    result["photos"] = [
        {
            "id": str(item[0]),
            "mime_type": item[1],
            "byte_size": item[2],
            "width": item[3],
            "height": item[4],
            "position": item[5],
            "is_main": item[6],
        }
        for item in photos
    ]
    result["location"] = (
        None
        if location is None
        else {
            "catalog_location_id": str(location[0]),
            "city": location[1],
            "district": location[2],
            "source": location[3],
            "updated_at": location[4].isoformat(),
        }
    )
    result["consents"] = [
        {
            "purpose": item[0],
            "granted": item[1],
            "policy_version": item[2],
            "occurred_at": item[3].isoformat(),
        }
        for item in consents
    ]
    return result
