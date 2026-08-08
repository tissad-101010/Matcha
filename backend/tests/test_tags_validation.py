"""Unit tests for bounded and normalized tag transfers."""

import pytest

from app.auth.validation import InputValidationError
from app.tags.validation import validate_new_tag, validate_tag_ids, validate_tag_query


def test_tag_query_is_normalized_and_bounded() -> None:
    assert validate_tag_query("  CinÉma ", "12") == ("cinéma", 12)
    with pytest.raises(InputValidationError):
        validate_tag_query("ok", "21")


def test_new_tag_collapses_whitespace() -> None:
    assert validate_new_tag({"name": "  jeux   vidéo "}) == ("jeux vidéo", "jeux vidéo")


def test_profile_tags_must_be_non_empty_unique_uuids() -> None:
    value = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
    assert str(validate_tag_ids({"tag_ids": [value]})[0]) == value
    with pytest.raises(InputValidationError):
        validate_tag_ids({"tag_ids": [value, value]})
