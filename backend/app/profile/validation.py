"""Validation for editable profile identity fields."""

from datetime import date
from typing import Any

from app.auth.validation import InputValidationError

ALLOWED_FIELDS = {"first_name", "last_name", "birth_date", "gender", "bio"}
GENDERS = {"man", "woman", "non_binary"}


def validate_profile_update(payload: Any, today: date | None = None) -> dict[str, Any]:
    """Validate a partial UpdateProfileRequest and reject hidden extra fields."""
    if not isinstance(payload, dict) or not payload:
        raise InputValidationError({"body": "Une modification JSON est requise."})
    extra = set(payload) - ALLOWED_FIELDS
    if extra:
        raise InputValidationError({"body": "Un ou plusieurs champs ne sont pas autorisés."})
    result: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for field in ("first_name", "last_name"):
        if field in payload:
            value = payload[field].strip() if isinstance(payload[field], str) else ""
            if not 1 <= len(value) <= 80:
                errors[field] = "Ce champ doit contenir entre 1 et 80 caractères."
            result[field] = value
    if "gender" in payload:
        if payload["gender"] not in GENDERS:
            errors["gender"] = "Genre invalide."
        result["gender"] = payload["gender"]
    if "bio" in payload:
        bio = payload["bio"].strip() if isinstance(payload["bio"], str) else ""
        if not 1 <= len(bio) <= 1000:
            errors["bio"] = "La biographie doit contenir entre 1 et 1000 caractères."
        result["bio"] = bio
    if "birth_date" in payload:
        result["birth_date"] = _adult_date(payload["birth_date"], today or date.today(), errors)
    if errors:
        raise InputValidationError(errors)
    return result


def _adult_date(value: Any, today: date, errors: dict[str, str]) -> date:
    try:
        parsed = date.fromisoformat(value) if isinstance(value, str) else date.min
    except ValueError:
        parsed = date.min
    try:
        cutoff = today.replace(year=today.year - 18)
    except ValueError:
        cutoff = today.replace(year=today.year - 18, day=28)
    if parsed == date.min or parsed > cutoff:
        errors["birth_date"] = "Vous devez avoir au moins 18 ans."
    return parsed
