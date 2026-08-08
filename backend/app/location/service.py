"""GPS reduction policy independent from HTTP and persistence details."""

from math import asin, cos, radians, sin, sqrt
from typing import Any
from uuid import UUID

from app.location.repository import catalogue_locations, save_location

MAX_CATALOGUE_DISTANCE_KM = 100.0


class UnsupportedGpsAreaError(Exception):
    """Raised when the local catalogue cannot approximate a GPS position safely."""


def save_reduced_gps(
    database_url: str, user_id: str, latitude: float, longitude: float
) -> dict[str, Any]:
    """Map transient raw coordinates to one coarse catalogue centroid."""
    locations = catalogue_locations(database_url)
    if not locations:
        raise UnsupportedGpsAreaError
    closest = min(
        locations,
        key=lambda row: _distance_km(latitude, longitude, float(row[4]), float(row[5])),
    )
    distance = _distance_km(latitude, longitude, float(closest[4]), float(closest[5]))
    if distance > MAX_CATALOGUE_DISTANCE_KM:
        raise UnsupportedGpsAreaError
    return save_location(database_url, user_id, UUID(str(closest[0])), "gps_reduced")


def _distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Compute a Haversine distance only to choose an approximate local centroid."""
    lat_a_r, lon_a_r, lat_b_r, lon_b_r = map(radians, (lat_a, lon_a, lat_b, lon_b))
    latitude_delta = lat_b_r - lat_a_r
    longitude_delta = lon_b_r - lon_a_r
    value = (
        sin(latitude_delta / 2) ** 2 + cos(lat_a_r) * cos(lat_b_r) * sin(longitude_delta / 2) ** 2
    )
    return 6371.0 * 2 * asin(sqrt(value))
