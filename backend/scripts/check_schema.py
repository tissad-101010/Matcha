"""Verify mandatory database invariants without retaining test data."""

import os
from collections.abc import Sequence
from typing import Any
from uuid import UUID

import psycopg

USER_A = UUID("00000000-0000-4000-8000-000000000001")
USER_B = UUID("00000000-0000-4000-8000-000000000002")
USER_C = UUID("00000000-0000-4000-8000-000000000003")


def expect_rejected(
    connection: psycopg.Connection[Any], statement: str, parameters: Sequence[Any]
) -> None:
    """Assert that a statement is rejected by a database constraint."""
    try:
        with connection.transaction():
            connection.execute(statement, parameters)
    except psycopg.IntegrityError:
        return
    raise AssertionError(f"La contrainte attendue n'a pas rejeté : {statement}")


def insert_account(connection: psycopg.Connection[Any], user_id: UUID, suffix: str) -> None:
    """Insert the smallest valid account and profile for constraint checks."""
    connection.execute(
        """
        INSERT INTO accounts (id, email, username, password_hash)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, f"schema-{suffix}@example.test", f"schema-{suffix}", "x" * 32),
    )
    connection.execute(
        """
        INSERT INTO profiles (user_id, first_name, last_name, birth_date)
        VALUES (%s, 'Schema', 'Check', DATE '1990-01-01')
        """,
        (user_id,),
    )


def check_metadata(connection: psycopg.Connection[Any]) -> None:
    """Check migration count and the privacy boundary of the public view."""
    migration_count = connection.execute("SELECT count(*) FROM schema_migrations").fetchone()
    assert migration_count == (15,)

    public_columns = {
        row[0]
        for row in connection.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'public_profiles'
            """
        )
    }
    forbidden = {"email", "birth_date", "reduced_latitude", "reduced_longitude"}
    assert public_columns.isdisjoint(forbidden)


def check_relationship_constraints(connection: psycopg.Connection[Any]) -> None:
    """Check self-interaction and canonical-pair protections."""
    expect_rejected(
        connection,
        "INSERT INTO visits (visitor_user_id, visited_user_id) VALUES (%s, %s)",
        (USER_A, USER_A),
    )
    expect_rejected(
        connection,
        "INSERT INTO likes (source_user_id, target_user_id) VALUES (%s, %s)",
        (USER_A, USER_A),
    )
    expect_rejected(
        connection,
        "INSERT INTO blocks (blocker_user_id, blocked_user_id) VALUES (%s, %s)",
        (USER_A, USER_A),
    )
    expect_rejected(
        connection,
        "INSERT INTO matches (user_low_id, user_high_id) VALUES (%s, %s)",
        (USER_B, USER_A),
    )

    connection.execute(
        "INSERT INTO matches (user_low_id, user_high_id) VALUES (%s, %s)",
        (USER_A, USER_B),
    )
    expect_rejected(
        connection,
        "INSERT INTO matches (user_low_id, user_high_id) VALUES (%s, %s)",
        (USER_A, USER_B),
    )


def check_photo_constraints(connection: psycopg.Connection[Any]) -> None:
    """Check the main-photo invariant and the strict five-photo limit."""
    try:
        with connection.transaction():
            connection.execute(
                """
                INSERT INTO photos (
                    user_id, object_key, mime_type, byte_size, width, height, position, is_main
                ) VALUES (%s, 'invalid/no-main.webp', 'image/webp', 100, 10, 10, 1, false)
                """,
                (USER_C,),
            )
            connection.execute("SET CONSTRAINTS photos_require_main IMMEDIATE")
    except psycopg.Error:
        pass
    else:
        raise AssertionError("Une collection de photos sans principale a été acceptée")

    for position in range(1, 6):
        connection.execute(
            """
            INSERT INTO photos (
                user_id, object_key, mime_type, byte_size, width, height, position, is_main
            ) VALUES (%s, %s, 'image/webp', 100, 10, 10, %s, %s)
            """,
            (USER_A, f"schema/photo-{position}.webp", position, position == 1),
        )
    expect_rejected(
        connection,
        """
        INSERT INTO photos (
            user_id, object_key, mime_type, byte_size, width, height, position, is_main
        ) VALUES (%s, 'schema/photo-6.webp', 'image/webp', 100, 10, 10, 6, false)
        """,
        (USER_A,),
    )


def main() -> int:
    """Run checks inside a transaction that is always rolled back."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL est obligatoire")

    with psycopg.connect(database_url) as connection:
        check_metadata(connection)
        for user_id, suffix in ((USER_A, "a"), (USER_B, "b"), (USER_C, "c")):
            insert_account(connection, user_id, suffix)
        check_relationship_constraints(connection)
        check_photo_constraints(connection)
        connection.rollback()

    print("Contrat du schéma validé, aucune donnée de test conservée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
