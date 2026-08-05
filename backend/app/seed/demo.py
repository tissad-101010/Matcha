"""Create the mandatory deterministic demonstration population."""

from datetime import UTC, datetime
from random import Random

import psycopg
from faker import Faker

from app.auth.passwords import hash_password, verify_password
from app.seed.fixtures import BIOS, LOCATIONS, TAGS
from app.seed.identifiers import stable_id
from app.seed.storage import s3_client, upload_avatars

PROFILE_COUNT = 600
DEMO_PASSWORD = "Brume-7-Rivière!"
GENDERS = ("man", "woman", "non_binary")


def build_profiles() -> list[dict[str, object]]:
    """Generate deterministic identities and profile attributes."""
    faker = Faker("fr_FR")
    faker.seed_instance(42)
    random = Random(42)
    profiles = []

    for index in range(PROFILE_COUNT):
        first_name = faker.first_name()
        last_name = faker.last_name()
        profiles.append(
            {
                "index": index,
                "id": stable_id("user", index),
                "email": f"demo{index:03d}@example.test",
                "username": f"demo{index:03d}",
                "first_name": first_name,
                "last_name": last_name,
                "birth_date": faker.date_of_birth(minimum_age=18, maximum_age=62),
                "gender": GENDERS[index % len(GENDERS)],
                "bio": BIOS[index % len(BIOS)],
                "location_index": index % len(LOCATIONS),
                "tag_indexes": random.sample(range(len(TAGS)), k=3 + index % 3),
            }
        )
    return profiles


def _insert_many(connection, statement: str, rows: list[tuple[object, ...]]) -> None:
    """Execute a parameterized statement for every fixture row."""
    connection.cursor().executemany(statement, rows)


def seed_database(database_url: str, config: dict[str, object]) -> str:
    """Populate an empty database or recognize an already complete demo seed."""
    profiles = build_profiles()
    expected_ids = [profile["id"] for profile in profiles]

    with psycopg.connect(database_url) as connection:
        existing = connection.execute("SELECT count(*) FROM accounts").fetchone()[0]
        seeded = connection.execute(
            "SELECT count(*) FROM accounts WHERE id = ANY(%s)", (expected_ids,)
        ).fetchone()[0]
        if existing == PROFILE_COUNT and seeded == PROFILE_COUNT:
            current_hash = connection.execute(
                "SELECT password_hash FROM accounts WHERE id = %s", (expected_ids[0],)
            ).fetchone()[0]
            if not verify_password(current_hash, DEMO_PASSWORD):
                connection.execute(
                    "UPDATE accounts SET password_hash = %s WHERE id = ANY(%s)",
                    (hash_password(DEMO_PASSWORD), expected_ids),
                )
            return "already_seeded"
        if existing:
            raise RuntimeError(
                "La base contient déjà des comptes : seed refusé sans reset explicite"
            )

    photo_rows = upload_avatars(s3_client(config), profiles)
    now = datetime.now(UTC)
    password_hash = hash_password(DEMO_PASSWORD)

    with psycopg.connect(database_url) as connection:
        _insert_catalogues(connection)
        _insert_profiles(connection, profiles, password_hash, now)
        _insert_profile_details(connection, profiles, photo_rows, now)
    return "created"


def _insert_catalogues(connection) -> None:
    location_rows = [
        (stable_id("location", key), country, city, district, key, latitude, longitude)
        for key, country, city, district, latitude, longitude in LOCATIONS
    ]
    _insert_many(
        connection,
        """INSERT INTO location_catalog (
            id, country_code, city_name, district_name, normalized_label,
            centroid_latitude, centroid_longitude
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        location_rows,
    )
    _insert_many(
        connection,
        "INSERT INTO tags (id, name, normalized_name) VALUES (%s, %s, %s)",
        [(stable_id("tag", index), tag, tag.casefold()) for index, tag in enumerate(TAGS)],
    )


def _insert_profiles(connection, profiles, password_hash: str, now: datetime) -> None:
    account_rows = [
        (p["id"], p["email"], p["username"], password_hash, now, now, now, now)
        for p in profiles
    ]
    _insert_many(
        connection,
        """INSERT INTO accounts (
            id, email, username, password_hash, status, email_verified_at,
            last_login_at, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, 'active', %s, %s, %s, %s)""",
        account_rows,
    )
    _insert_many(
        connection,
        """INSERT INTO profiles (
            user_id, first_name, last_name, birth_date, gender, bio
        ) VALUES (%s, %s, %s, %s, %s, %s)""",
        [
            (p["id"], p["first_name"], p["last_name"], p["birth_date"], p["gender"], p["bio"])
            for p in profiles
        ],
    )


def _insert_profile_details(connection, profiles, photo_rows, now: datetime) -> None:
    consent_rows = [(profile["id"], "matching_preferences") for profile in profiles]
    consent_rows.extend(
        (profile["id"], "gps_location")
        for profile in profiles
        if int(profile["index"]) % 4 == 0
    )
    _insert_many(
        connection,
        """INSERT INTO consent_events (user_id, purpose, policy_version, granted)
        VALUES (%s, %s, 'demo-v1', true)""",
        consent_rows,
    )
    preference_rows = []
    for profile in profiles:
        profile_index = int(profile["index"])
        desired = GENDERS if profile_index % 4 == 0 else (GENDERS[(profile_index + 1) % 3],)
        preference_rows.extend((profile["id"], gender) for gender in desired)
    _insert_many(
        connection,
        "INSERT INTO user_preferences VALUES (%s, %s, CURRENT_TIMESTAMP)",
        preference_rows,
    )
    _insert_many(
        connection,
        "INSERT INTO profile_tags (user_id, tag_id) VALUES (%s, %s)",
        [
            (p["id"], stable_id("tag", tag_index))
            for p in profiles
            for tag_index in p["tag_indexes"]
        ],
    )
    _insert_many(
        connection,
        """INSERT INTO user_locations (
            user_id, catalog_location_id, source, reduced_latitude, reduced_longitude, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s)""",
        [_location_row(profile, now) for profile in profiles],
    )
    _insert_many(
        connection,
        "INSERT INTO profile_stats (user_id) VALUES (%s)",
        [(p["id"],) for p in profiles],
    )
    _insert_many(
        connection,
        """INSERT INTO photos (
            id, user_id, object_key, mime_type, byte_size, width, height, position, is_main
        ) VALUES (%s, %s, %s, 'image/webp', %s, %s, %s, %s, %s)""",
        photo_rows,
    )


def _location_row(profile: dict[str, object], now: datetime) -> tuple[object, ...]:
    """Build one location row without exposing exact coordinates publicly."""
    location = LOCATIONS[int(profile["location_index"])]
    return (
        profile["id"],
        stable_id("location", location[0]),
        "gps_reduced" if int(profile["index"]) % 4 == 0 else "manual",
        location[4],
        location[5],
        now,
    )
