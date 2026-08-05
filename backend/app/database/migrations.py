"""Discover and transactionally apply immutable SQL migrations."""

import hashlib
from pathlib import Path

import psycopg

LOCK_ID = 1_297_324_821


def migration_files(directory: Path) -> list[Path]:
    """Return ordered SQL files and reject an empty migration directory."""
    files = sorted(directory.glob("[0-9][0-9][0-9]_*.sql"))
    if not files:
        raise RuntimeError(f"Aucune migration trouvée dans {directory}")
    return files


def checksum(path: Path) -> str:
    """Calculate the immutable fingerprint stored after application."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_migrations(database_url: str, directory: Path) -> int:
    """Apply pending files transactionally and return their count."""
    files = migration_files(directory)
    applied_count = 0

    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute("SELECT pg_advisory_lock(%s)", (LOCK_ID,))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version text PRIMARY KEY,
                checksum text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        rows = connection.execute(
            "SELECT version, checksum FROM schema_migrations ORDER BY version"
        ).fetchall()
        applied = dict(rows)

        missing_files = set(applied) - {path.name for path in files}
        if missing_files:
            raise RuntimeError(f"Fichiers de migration manquants : {sorted(missing_files)}")

        for path in files:
            file_checksum = checksum(path)
            if path.name in applied:
                if applied[path.name] != file_checksum:
                    raise RuntimeError(f"Migration déjà appliquée mais modifiée : {path.name}")
                continue

            with connection.transaction():
                connection.execute(path.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                    (path.name, file_checksum),
                )
            applied_count += 1
            print(f"Migration appliquée : {path.name}")

    return applied_count
