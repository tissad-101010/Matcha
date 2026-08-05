"""Command-line entry point for SQL migrations."""

import os
from pathlib import Path

from app.database.migrations import apply_migrations

MIGRATIONS_PATH = Path(os.getenv("MIGRATIONS_PATH", "/app/database/migrations"))


def main() -> int:
    """Load configuration and report a concise migration result."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL est obligatoire")
    count = apply_migrations(database_url, MIGRATIONS_PATH)
    print(f"Schéma à jour ({count} nouvelle(s) migration(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
