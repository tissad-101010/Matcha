"""Tests for endpoints that do not require infrastructure services."""

from flask import Flask
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


def test_ready_health_returns_dependency_states(app: Flask, client: FlaskClient) -> None:
    app.config["READINESS_CHECK"] = lambda _config: {
        "postgres": True,
        "valkey": True,
        "minio": True,
    }

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.get_json() == {
        "data": {
            "status": "ready",
            "checks": {"postgres": True, "valkey": True, "minio": True},
        }
    }


def test_ready_health_fails_when_a_dependency_is_down(app: Flask, client: FlaskClient) -> None:
    app.config["READINESS_CHECK"] = lambda _config: {
        "postgres": True,
        "valkey": False,
        "minio": True,
    }

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.get_json()["data"]["status"] == "unavailable"
