"""Explicit mutual gender compatibility rules required by the subject."""

from collections.abc import Collection

GENDERS = frozenset({"man", "woman", "non_binary"})


def effective_preferences(stored: Collection[str]) -> frozenset[str]:
    """Treat an absent stored preference as every supported gender."""
    return frozenset(stored) if stored else GENDERS


def mutually_compatible(
    viewer_gender: str,
    viewer_preferences: Collection[str],
    candidate_gender: str,
    candidate_preferences: Collection[str],
) -> bool:
    """Require each member's gender to belong to the other's effective set."""
    if viewer_gender not in GENDERS or candidate_gender not in GENDERS:
        return False
    return candidate_gender in effective_preferences(
        viewer_preferences
    ) and viewer_gender in effective_preferences(candidate_preferences)
