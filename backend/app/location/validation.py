"""Validation for local catalogue and temporary GPS transfers."""

import math
from typing import Any
from uuid import UUID

from app.auth.validation import InputValidationError


def validate_location_query(value: str | None, limit_value: str | None) -> tuple[str, int]:
    """Normalize a bounded local-catalogue search."""
    query = (value or "").strip().lower()
    if len(query) > 120:
        raise InputValidationError({"query": "La recherche est limitée à 120 caractères."})
    try:
        limit = int(limit_value or "20")
    except ValueError as error:
        raise InputValidationError({"limit": "La limite doit être un entier."}) from error
    if not 1 <= limit <= 20:
        raise InputValidationError({"limit": "La limite doit être comprise entre 1 et 20."})
    return query, limit


def validate_manual_location(payload: Any) -> UUID:
    """Accept exactly one catalogue UUID."""
    value = payload.get("catalog_location_id") if isinstance(payload, dict) else None
    try:
        return UUID(value) if isinstance(value, str) else _invalid_uuid()
    except ValueError as error:
        raise InputValidationError(
            {"catalog_location_id": "Sélectionnez une localisation proposée."}
        ) from error


def validate_gps_location(payload: Any) -> tuple[float, float]:
    """Accept finite browser coordinates without retaining the raw values."""
    if not isinstance(payload, dict):
        raise InputValidationError({"body": "Des coordonnées JSON sont requises."})
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if (
        isinstance(latitude, bool)
        or not isinstance(latitude, int | float)
        or not math.isfinite(latitude)
        or not -90 <= latitude <= 90
    ):
        raise InputValidationError({"latitude": "La latitude doit être comprise entre -90 et 90."})
    if (
        isinstance(longitude, bool)
        or not isinstance(longitude, int | float)
        or not math.isfinite(longitude)
        or not -180 <= longitude <= 180
    ):
        raise InputValidationError(
            {"longitude": "La longitude doit être comprise entre -180 et 180."}
        )
    return float(latitude), float(longitude)


def _invalid_uuid() -> UUID:
    raise InputValidationError({"catalog_location_id": "Sélectionnez une localisation proposée."})
