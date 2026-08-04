"""Tests for endpoints that do not require infrastructure services."""

from flask.testing import FlaskClient


def test_live_health_returns_stable_json(client: FlaskClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.get_json() == {"data": {"status": "ok"}}


def test_unknown_route_uses_json_error_contract(client: FlaskClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "not_found",
            "message": "The requested URL was not found on the server. If you entered the URL "
            "manually please check your spelling and try again.",
        }
    }
