"""Ranking tests for transparent mandatory suggestions."""

from datetime import UTC, datetime
from uuid import UUID

from app.discovery.repository import Candidate, ViewerContext
from app.discovery.service import suggestions
from app.discovery.validation import DiscoveryQuery


def candidate(
    number: int,
    *,
    location_id: UUID,
    latitude: float,
    popularity: int,
    tags: frozenset[UUID],
    preferences: tuple[str, ...] = ("woman",),
) -> Candidate:
    return Candidate(
        UUID(int=number),
        f"Profil {number}",
        30,
        "man",
        preferences,
        latitude,
        2.35,
        location_id,
        "Paris" if latitude > 48 else "Lyon",
        None,
        popularity,
        datetime.now(UTC),
        UUID(int=number + 100),
        ({"id": str(next(iter(tags))), "name": "cinéma"},),
        tags,
    )


def test_same_zone_has_absolute_priority_then_score(monkeypatch) -> None:
    paris_id, lyon_id, tag_id = UUID(int=10), UUID(int=11), UUID(int=12)
    viewer = ViewerContext(
        "woman", ("man",), 48.8566, 2.35, paris_id, "Paris", None, frozenset({tag_id})
    )
    far_same_zone = candidate(
        1, location_id=paris_id, latitude=47.9, popularity=0, tags=frozenset({tag_id})
    )
    close_other_zone = candidate(
        2, location_id=lyon_id, latitude=48.85, popularity=100, tags=frozenset({tag_id})
    )
    monkeypatch.setattr("app.discovery.service.load_viewer", lambda *_args: viewer)
    monkeypatch.setattr(
        "app.discovery.service.load_eligible_candidates",
        lambda *_args: [close_other_zone, far_same_zone],
    )

    result = suggestions("database", "viewer", DiscoveryQuery(0, 20))

    assert [item["id"] for item in result["data"]] == [str(UUID(int=1)), str(UUID(int=2))]
    assert result["data"][0]["location"]["same_zone"] is True
    assert "latitude" not in result["data"][0]["location"]


def test_incompatible_candidate_is_removed_and_page_is_bounded(monkeypatch) -> None:
    location_id, tag_id = UUID(int=10), UUID(int=12)
    viewer = ViewerContext(
        "woman", ("man",), 48.8566, 2.35, location_id, "Paris", None, frozenset({tag_id})
    )
    compatible = candidate(
        1, location_id=location_id, latitude=48.85, popularity=10, tags=frozenset({tag_id})
    )
    incompatible = candidate(
        2,
        location_id=location_id,
        latitude=48.85,
        popularity=100,
        tags=frozenset({tag_id}),
        preferences=("man",),
    )
    monkeypatch.setattr("app.discovery.service.load_viewer", lambda *_args: viewer)
    monkeypatch.setattr(
        "app.discovery.service.load_eligible_candidates",
        lambda *_args: [compatible, incompatible],
    )
    result = suggestions("database", "viewer", DiscoveryQuery(0, 1))
    assert result["meta"] == {"next_cursor": None, "count": 1}
    assert result["data"][0]["common_tags"] == 1
