"""Tests for opaque authentication tokens."""

from app.auth.tokens import create_token, token_hash


def test_token_is_random_and_only_its_hash_is_reproducible() -> None:
    first, first_hash = create_token()
    second, second_hash = create_token()

    assert first != second
    assert first_hash != second_hash
    assert first_hash == token_hash(first)
    assert len(first_hash) == 32
