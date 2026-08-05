"""Tests for deterministic, synthetic demonstration fixtures."""

from app.auth.passwords import password_error
from app.seed.avatars import avatar_bytes
from app.seed.demo import DEMO_PASSWORD, PROFILE_COUNT, build_profiles
from app.seed.identifiers import stable_id


def test_profiles_are_deterministic_and_distinct() -> None:
    first = build_profiles()
    second = build_profiles()

    assert len(first) == PROFILE_COUNT
    assert first == second
    assert len({profile["id"] for profile in first}) == PROFILE_COUNT
    assert len({profile["email"] for profile in first}) == PROFILE_COUNT


def test_stable_ids_are_namespaced_by_kind() -> None:
    assert stable_id("user", 1) == stable_id("user", 1)
    assert stable_id("user", 1) != stable_id("photo", 1)


def test_avatar_is_deterministic_webp_without_metadata() -> None:
    first = avatar_bytes(42)

    assert first == avatar_bytes(42)
    assert first != avatar_bytes(43)
    assert first.startswith(b"RIFF") and b"WEBP" in first[:16]


def test_demo_password_respects_the_registration_policy() -> None:
    assert password_error(DEMO_PASSWORD) is None
