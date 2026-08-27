"""Transparent multi-criterion ranking for compatible suggestions."""

from datetime import UTC, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Any

from app.discovery.compatibility import mutually_compatible
from app.discovery.repository import Candidate, load_eligible_candidates, load_viewer
from app.discovery.validation import DiscoveryQuery


class DiscoveryUnavailableError(Exception):
    """Raised when the current member is not eligible for discovery."""


def suggestions(database_url: str, user_id: str, query: DiscoveryQuery) -> dict[str, Any]:
    """Rank every eligible candidate, then return one bounded stable page."""
    viewer = load_viewer(database_url, user_id)
    if viewer is None:
        raise DiscoveryUnavailableError
    ranked = []
    for candidate in load_eligible_candidates(database_url, user_id):
        if not mutually_compatible(
            viewer.gender, viewer.preferences, candidate.gender, candidate.preferences
        ):
            continue
        distance = _distance_km(
            viewer.latitude, viewer.longitude, candidate.latitude, candidate.longitude
        )
        common_tags = len(viewer.tag_ids & candidate.tag_ids)
        same_zone = viewer.location_id == candidate.location_id
        if not _matches_filters(candidate, distance, viewer.tag_ids, query):
            continue
        score = _score(distance, common_tags, candidate.popularity)
        ranked.append((not same_zone, -score, distance, str(candidate.id), candidate, common_tags))
    ranked.sort(key=lambda item: _sort_key(item, query.sort))
    page = ranked[query.offset : query.offset + query.limit]
    next_offset = query.offset + query.limit if query.offset + query.limit < len(ranked) else None
    return {
        "data": [_profile_card(item[4], item[2], not item[0], item[5]) for item in page],
        "meta": {
            "next_cursor": str(next_offset) if next_offset is not None else None,
            "count": len(page),
        },
    }


def _matches_filters(
    candidate: Candidate, distance: float, viewer_tags: frozenset, query: DiscoveryQuery
) -> bool:
    return not (
        (query.age_min is not None and candidate.age < query.age_min)
        or (query.age_max is not None and candidate.age > query.age_max)
        or (query.distance_max_km is not None and distance > query.distance_max_km)
        or (query.popularity_min is not None and candidate.popularity < query.popularity_min)
        or (query.popularity_max is not None and candidate.popularity > query.popularity_max)
        or (query.tag_ids and not query.tag_ids <= candidate.tag_ids & viewer_tags)
    )


def _sort_key(item: tuple, sort: str) -> tuple:
    same_zone, negative_score, distance, identifier, candidate, common_tags = item
    if sort == "age":
        return (candidate.age, distance, identifier)
    if sort == "distance":
        return (distance, identifier)
    if sort == "popularity":
        return (-candidate.popularity, distance, identifier)
    if sort == "tags":
        return (-common_tags, distance, identifier)
    return (same_zone, negative_score, distance, identifier)


def _score(distance_km: float, common_tags: int, popularity: int) -> float:
    proximity = max(0.0, 1.0 - distance_km / 100.0)
    tags = min(common_tags / 5.0, 1.0)
    return 0.50 * proximity + 0.30 * tags + 0.20 * (popularity / 100.0)


def _distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    lat_a_r, lon_a_r, lat_b_r, lon_b_r = map(radians, (lat_a, lon_a, lat_b, lon_b))
    lat_delta = lat_b_r - lat_a_r
    lon_delta = lon_b_r - lon_a_r
    value = sin(lat_delta / 2) ** 2 + cos(lat_a_r) * cos(lat_b_r) * sin(lon_delta / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(value))


def _profile_card(
    candidate: Candidate, distance: float, same_zone: bool, common_tags: int
) -> dict[str, Any]:
    last_seen = candidate.last_seen_at
    online = bool(last_seen and last_seen >= datetime.now(UTC) - timedelta(minutes=2))
    return {
        "id": str(candidate.id),
        "first_name": candidate.first_name,
        "age": candidate.age,
        "main_photo": None
        if candidate.photo_id is None
        else {
            "id": str(candidate.photo_id),
            "url": f"/api/v1/photos/{candidate.photo_id}",
            "position": 1,
            "is_main": True,
        },
        "tags": list(candidate.tags),
        "location": {
            "city": candidate.city,
            "district": candidate.district,
            "distance_km": round(distance, 1),
            "same_zone": same_zone,
        },
        "popularity": candidate.popularity,
        "presence": {
            "online": online,
            "last_seen_at": last_seen.isoformat() if last_seen else None,
        },
        "common_tags": common_tags,
    }
