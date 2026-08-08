"""Profile completeness rules shared by onboarding and matching."""

from typing import Any

from app.profile.repository import get_private_profile


def private_profile(database_url: str, user_id: str) -> dict[str, Any] | None:
    """Add explicit missing fields and completeness to the private aggregate."""
    profile = get_private_profile(database_url, user_id)
    if profile is None:
        return None
    missing: list[str] = []
    for field in ("gender", "bio"):
        if not profile[field]:
            missing.append(field)
    if not profile["tags"]:
        missing.append("tags")
    if profile["location"] is None:
        missing.append("location")
    profile["missing_profile_fields"] = missing
    profile["profile_complete"] = not missing
    return profile
