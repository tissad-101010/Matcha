"""Ranking and filtering tests for transparent mandatory suggestions."""

from dataclasses import replace
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


def test_filters_are_combined_before_pagination(monkeypatch) -> None:
    location_id, tag_id = UUID(int=10), UUID(int=12)
    viewer = ViewerContext(
        "woman", ("man",), 48.8566, 2.35, location_id, "Paris", None, frozenset({tag_id})
    )
    accepted = replace(
        candidate(
            1, location_id=location_id, latitude=48.85, popularity=70, tags=frozenset({tag_id})
        ),
        age=35,
    )
    too_young = replace(accepted, id=UUID(int=2), age=24)
    too_popular = replace(accepted, id=UUID(int=3), popularity=95)
    monkeypatch.setattr("app.discovery.service.load_viewer", lambda *_args: viewer)
    monkeypatch.setattr(
        "app.discovery.service.load_eligible_candidates",
        lambda *_args: [too_young, too_popular, accepted],
    )
    query = DiscoveryQuery(age_min=30, popularity_max=80, tag_ids=frozenset({tag_id}))
    result = suggestions("database", "viewer", query)
    assert [item["id"] for item in result["data"]] == [str(accepted.id)]


def test_explicit_sort_overrides_recommended_same_zone_priority(monkeypatch) -> None:
    paris_id, lyon_id, tag_id = UUID(int=10), UUID(int=11), UUID(int=12)
    viewer = ViewerContext(
        "woman", ("man",), 48.8566, 2.35, paris_id, "Paris", None, frozenset({tag_id})
    )
    older_same_zone = replace(
        candidate(1, location_id=paris_id, latitude=48.85, popularity=10, tags=frozenset({tag_id})),
        age=45,
    )
    younger_other_zone = replace(
        candidate(2, location_id=lyon_id, latitude=45.75, popularity=80, tags=frozenset({tag_id})),
        age=25,
    )
    monkeypatch.setattr("app.discovery.service.load_viewer", lambda *_args: viewer)
    monkeypatch.setattr(
        "app.discovery.service.load_eligible_candidates",
        lambda *_args: [older_same_zone, younger_other_zone],
    )
    result = suggestions("database", "viewer", DiscoveryQuery(sort="age"))
    assert [item["id"] for item in result["data"]] == [
        str(younger_other_zone.id),
        str(older_same_zone.id),
    ]


def test_search_location_filter_keeps_only_the_requested_zone(monkeypatch) -> None:
    paris_id, lyon_id, tag_id = UUID(int=10), UUID(int=11), UUID(int=12)
    viewer = ViewerContext(
        "woman", ("man",), 48.8566, 2.35, paris_id, "Paris", None, frozenset({tag_id})
    )
    paris = candidate(
        1, location_id=paris_id, latitude=48.85, popularity=10, tags=frozenset({tag_id})
    )
    lyon = candidate(
        2, location_id=lyon_id, latitude=45.75, popularity=80, tags=frozenset({tag_id})
    )
    monkeypatch.setattr("app.discovery.service.load_viewer", lambda *_args: viewer)
    monkeypatch.setattr(
        "app.discovery.service.load_eligible_candidates", lambda *_args: [paris, lyon]
    )
    result = suggestions("database", "viewer", DiscoveryQuery(location_id=lyon_id))
    assert [item["id"] for item in result["data"]] == [str(lyon.id)]
