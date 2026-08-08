"""Tests proving raw GPS data is replaced by a coarse catalogue identifier."""

from uuid import UUID

import pytest

from app.location.service import UnsupportedGpsAreaError, save_reduced_gps

PARIS_ID = UUID("e8d7a810-4cb8-47ec-b359-70fdc5288a9a")


def test_gps_uses_the_nearest_catalogue_centroid(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.location.service.catalogue_locations",
        lambda _url: [
            (PARIS_ID, "Paris", None, "FR", 48.8566, 2.3522),
            (UUID(int=2), "Lyon", None, "FR", 45.764, 4.8357),
        ],
    )
    saved: list[tuple[UUID, str]] = []
    monkeypatch.setattr(
        "app.location.service.save_location",
        lambda _url, _user, location_id, source: (
            saved.append((location_id, source)) or {"city": "Paris"}
        ),
    )

    result = save_reduced_gps("database", "user", 48.86, 2.35)

    assert result == {"city": "Paris"}
    assert saved == [(PARIS_ID, "gps_reduced")]


def test_gps_outside_the_local_catalogue_falls_back_to_manual(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.location.service.catalogue_locations",
        lambda _url: [(PARIS_ID, "Paris", None, "FR", 48.8566, 2.3522)],
    )
    with pytest.raises(UnsupportedGpsAreaError):
        save_reduced_gps("database", "user", 40.7128, -74.006)
