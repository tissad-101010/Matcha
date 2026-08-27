"""Strict, bounded validation for discovery filters and pagination."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from uuid import UUID

from app.auth.validation import InputValidationError

SORTS = frozenset({"recommended", "age", "distance", "popularity", "tags"})


@dataclass(frozen=True)
class DiscoveryQuery:
    offset: int = 0
    limit: int = 20
    sort: str = "recommended"
    age_min: int | None = None
    age_max: int | None = None
    distance_max_km: float | None = None
    popularity_min: int | None = None
    popularity_max: int | None = None
    tag_ids: frozenset[UUID] = frozenset()


def validate_discovery_query(
    values: Mapping[str, str | None], tag_values: Sequence[str] = ()
) -> DiscoveryQuery:
    """Validate allowlisted query values without silently accepting bad ranges."""
    errors: dict[str, str] = {}
    offset = _integer(values.get("cursor"), "cursor", 0, None, 0, errors)
    limit = _integer(values.get("limit"), "limit", 1, 50, 20, errors)
    sort = values.get("sort") or "recommended"
    if sort not in SORTS:
        errors["sort"] = "Tri invalide."
    age_min = _integer(values.get("age_min"), "age_min", 18, 120, None, errors)
    age_max = _integer(values.get("age_max"), "age_max", 18, 120, None, errors)
    popularity_min = _integer(values.get("popularity_min"), "popularity_min", 0, 100, None, errors)
    popularity_max = _integer(values.get("popularity_max"), "popularity_max", 0, 100, None, errors)
    distance = _number(values.get("distance_max_km"), "distance_max_km", 0, 20000, errors)
    _valid_range(age_min, age_max, "age_max", errors)
    _valid_range(popularity_min, popularity_max, "popularity_max", errors)
    tags: set[UUID] = set()
    raw_tags = [part for value in tag_values for part in value.split(",") if part]
    if len(raw_tags) > 20:
        errors["tag_ids"] = "Sélectionnez au maximum 20 tags."
    else:
        try:
            tags = {UUID(value) for value in raw_tags}
        except ValueError:
            errors["tag_ids"] = "Un identifiant de tag est invalide."
    if errors:
        raise InputValidationError(errors)
    return DiscoveryQuery(
        offset or 0,
        limit or 20,
        sort,
        age_min,
        age_max,
        distance,
        popularity_min,
        popularity_max,
        frozenset(tags),
    )


def _integer(value, name, minimum, maximum, default, errors):  # type: ignore[no-untyped-def]
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors[name] = "Nombre entier invalide."
        return default
    if parsed < minimum or (maximum is not None and parsed > maximum):
        errors[name] = "Valeur hors limites."
    return parsed


def _number(value, name, minimum, maximum, errors):  # type: ignore[no-untyped-def]
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        errors[name] = "Nombre invalide."
        return None
    if not isfinite(parsed) or not minimum <= parsed <= maximum:
        errors[name] = "Valeur hors limites."
    return parsed


def _valid_range(minimum, maximum, field, errors):  # type: ignore[no-untyped-def]
    if minimum is not None and maximum is not None and minimum > maximum:
        errors[field] = "La valeur maximale doit être supérieure ou égale au minimum."
