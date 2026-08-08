"""Validation for photo identifiers and metadata mutations."""

from typing import Any
from uuid import UUID

from app.auth.validation import InputValidationError


def validate_photo_id(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise InputValidationError({"photo_id": "Photo invalide."}) from error


def validate_photo_update(payload: Any) -> tuple[int | None, bool]:
    """Allow a position and/or an explicit request to make the photo main."""
    if not isinstance(payload, dict) or not payload or set(payload) - {"position", "is_main"}:
        raise InputValidationError({"body": "Modification de photo invalide."})
    position = payload.get("position")
    if position is not None and (
        isinstance(position, bool) or not isinstance(position, int) or not 1 <= position <= 5
    ):
        raise InputValidationError({"position": "La position doit être comprise entre 1 et 5."})
    is_main = payload.get("is_main", False)
    if not isinstance(is_main, bool) or ("is_main" in payload and not is_main):
        raise InputValidationError(
            {"is_main": "Une photo principale ne peut pas être désactivée sans remplaçante."}
        )
    return position, is_main
