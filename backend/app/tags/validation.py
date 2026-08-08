"""Validation and normalization for profile-tag transfers."""

from typing import Any
from uuid import UUID

from app.auth.validation import InputValidationError

MAX_PROFILE_TAGS = 10


def validate_tag_query(value: str | None, limit_value: str | None) -> tuple[str, int]:
    """Normalize a catalogue query and enforce its small bounded result set."""
    query = (value or "").strip().lower()
    if len(query) > 50:
        raise InputValidationError({"query": "La recherche est limitée à 50 caractères."})
    try:
        limit = int(limit_value or "20")
    except ValueError as error:
        raise InputValidationError({"limit": "La limite doit être un entier."}) from error
    if not 1 <= limit <= 20:
        raise InputValidationError({"limit": "La limite doit être comprise entre 1 et 20."})
    return query, limit


def validate_new_tag(payload: Any) -> tuple[str, str]:
    """Return the display name and its deterministic comparison form."""
    name = payload.get("name") if isinstance(payload, dict) else None
    name = " ".join(name.split()) if isinstance(name, str) else ""
    if not 1 <= len(name) <= 50:
        raise InputValidationError({"name": "Le tag doit contenir entre 1 et 50 caractères."})
    return name, name.lower()


def validate_tag_ids(payload: Any) -> list[UUID]:
    """Validate a non-empty, duplicate-free profile tag selection."""
    values = payload.get("tag_ids") if isinstance(payload, dict) else None
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_PROFILE_TAGS:
        raise InputValidationError({"tag_ids": f"Choisissez entre 1 et {MAX_PROFILE_TAGS} tags."})
    try:
        tag_ids = [UUID(value) for value in values if isinstance(value, str)]
    except ValueError as error:
        raise InputValidationError({"tag_ids": "Un identifiant de tag est invalide."}) from error
    if len(tag_ids) != len(values) or len(set(tag_ids)) != len(tag_ids):
        raise InputValidationError({"tag_ids": "Les tags doivent être valides et uniques."})
    return tag_ids
