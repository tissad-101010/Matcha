"""Bounded query validation for discovery pagination."""

from dataclasses import dataclass

from app.auth.validation import InputValidationError


@dataclass(frozen=True)
class DiscoveryQuery:
    offset: int
    limit: int


def validate_discovery_query(cursor: str | None, limit_value: str | None) -> DiscoveryQuery:
    """Use a small stable offset cursor until filtered search cursors are introduced."""
    try:
        offset = int(cursor or "0")
        limit = int(limit_value or "20")
    except ValueError as error:
        raise InputValidationError({"cursor": "Pagination invalide."}) from error
    if offset < 0:
        raise InputValidationError({"cursor": "Pagination invalide."})
    if not 1 <= limit <= 50:
        raise InputValidationError({"limit": "La limite doit être comprise entre 1 et 50."})
    return DiscoveryQuery(offset, limit)
