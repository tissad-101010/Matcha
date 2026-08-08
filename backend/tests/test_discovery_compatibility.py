"""Business tests for mandatory mutual compatibility."""

import pytest

from app.discovery.compatibility import effective_preferences, mutually_compatible


def test_absent_preference_effectively_accepts_every_gender() -> None:
    assert effective_preferences([]) == {"man", "woman", "non_binary"}


@pytest.mark.parametrize(
    ("viewer_gender", "viewer_preferences", "candidate_gender", "candidate_preferences"),
    [
        ("man", ["woman"], "woman", ["man"]),
        ("woman", ["woman"], "woman", ["woman"]),
        ("non_binary", [], "man", ["non_binary"]),
        ("woman", ["man", "woman", "non_binary"], "non_binary", []),
    ],
)
def test_mutual_heterosexual_homosexual_and_broad_preferences_are_supported(
    viewer_gender: str,
    viewer_preferences: list[str],
    candidate_gender: str,
    candidate_preferences: list[str],
) -> None:
    assert mutually_compatible(
        viewer_gender, viewer_preferences, candidate_gender, candidate_preferences
    )


def test_one_sided_interest_is_not_compatible() -> None:
    assert not mutually_compatible("man", ["woman"], "woman", ["woman"])


def test_incomplete_gender_is_never_compatible() -> None:
    assert not mutually_compatible("", [], "woman", ["man"])
