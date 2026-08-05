"""Tests for the single authoritative profile completeness rule."""

from app.profile.service import private_profile


def test_private_profile_lists_missing_matching_fields(monkeypatch) -> None:
    stored = {"gender": "woman", "bio": None, "tags": [], "location": None}
    monkeypatch.setattr("app.profile.service.get_private_profile", lambda *_args: stored)

    result = private_profile("unused", "user-id")

    assert result["profile_complete"] is False
    assert result["missing_profile_fields"] == ["bio", "tags", "location"]
