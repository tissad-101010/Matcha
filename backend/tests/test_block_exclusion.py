"""Discovery and search share the bidirectional block exclusion."""

from unittest.mock import MagicMock

import pytest
from backend.scripts.check_block_exclusion import assert_excluded


def test_block_check_accepts_an_excluded_candidate(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.scripts.check_block_exclusion.load_eligible_candidates",
        lambda *_args: [],
    )
    assert_excluded("database", "viewer", "blocked")


def test_block_check_fails_if_repository_leaks_candidate(monkeypatch) -> None:
    candidate = MagicMock()
    candidate.id = "blocked"
    monkeypatch.setattr(
        "backend.scripts.check_block_exclusion.load_eligible_candidates",
        lambda *_args: [candidate],
    )
    with pytest.raises(RuntimeError, match="remains eligible"):
        assert_excluded("database", "viewer", "blocked")
