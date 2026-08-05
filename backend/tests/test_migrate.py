"""Unit tests for deterministic migration discovery and checksums."""

from pathlib import Path

import pytest

from app.database.migrations import checksum, migration_files


def test_migration_files_are_sorted_and_ignore_other_files(tmp_path: Path) -> None:
    (tmp_path / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "notes.md").write_text("ignored", encoding="utf-8")

    assert [path.name for path in migration_files(tmp_path)] == [
        "001_first.sql",
        "002_second.sql",
    ]


def test_migration_files_reject_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Aucune migration"):
        migration_files(tmp_path)


def test_checksum_changes_with_file_content(tmp_path: Path) -> None:
    migration = tmp_path / "001_example.sql"
    migration.write_text("SELECT 1;", encoding="utf-8")
    first_checksum = checksum(migration)

    migration.write_text("SELECT 2;", encoding="utf-8")

    assert checksum(migration) != first_checksum
