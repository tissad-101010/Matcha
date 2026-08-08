"""Unit tests for private location transfer validation."""

import pytest

from app.auth.validation import InputValidationError
from app.location.validation import (
    validate_gps_location,
    validate_location_query,
    validate_manual_location,
)


def test_catalogue_query_is_normalized_and_bounded() -> None:
    assert validate_location_query("  PARIS ", "5") == ("paris", 5)
    with pytest.raises(InputValidationError):
        validate_location_query("Paris", "0")


def test_manual_location_requires_a_uuid() -> None:
    value = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
    assert str(validate_manual_location({"catalog_location_id": value})) == value
    with pytest.raises(InputValidationError):
        validate_manual_location({"catalog_location_id": "Paris"})


@pytest.mark.parametrize(
    "payload",
    [
        {"latitude": True, "longitude": 2.35},
        {"latitude": 91, "longitude": 2.35},
        {"latitude": 48.85, "longitude": float("nan")},
        {"latitude": 48.85, "longitude": 181},
    ],
)
def test_gps_rejects_ambiguous_or_out_of_range_coordinates(payload) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(InputValidationError):
        validate_gps_location(payload)


def test_gps_returns_finite_coordinates() -> None:
    assert validate_gps_location({"latitude": 48.8566, "longitude": 2.3522}) == (
        48.8566,
        2.3522,
    )
