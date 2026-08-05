"""Validation tests for editable onboarding identity fields."""

from datetime import date

import pytest

from app.auth.validation import InputValidationError
from app.profile.validation import validate_consent, validate_preferences, validate_profile_update


def test_profile_update_accepts_only_documented_fields() -> None:
    result = validate_profile_update(
        {"gender": "non_binary", "bio": "  Une bio concise.  "},
        today=date(2026, 8, 5),
    )
    assert result == {"gender": "non_binary", "bio": "Une bio concise."}

    with pytest.raises(InputValidationError):
        validate_profile_update({"email": "hidden@example.test"})


def test_profile_birth_date_still_requires_adulthood() -> None:
    with pytest.raises(InputValidationError) as error:
        validate_profile_update({"birth_date": "2009-01-01"}, today=date(2026, 8, 5))

    assert "birth_date" in error.value.fields


def test_preferences_are_a_unique_gender_set() -> None:
    assert validate_preferences({"desired_genders": []}) == []
    assert validate_preferences({"desired_genders": ["woman", "non_binary"]}) == [
        "woman",
        "non_binary",
    ]
    with pytest.raises(InputValidationError):
        validate_preferences({"desired_genders": ["woman", "woman"]})


def test_consent_must_be_explicit_and_current() -> None:
    assert validate_consent({"confirmed": True, "policy_version": "2026-08"}, "2026-08")
    with pytest.raises(InputValidationError):
        validate_consent({"confirmed": False, "policy_version": "2026-08"}, "2026-08")
    with pytest.raises(InputValidationError):
        validate_consent({"confirmed": True, "policy_version": "old"}, "2026-08")
