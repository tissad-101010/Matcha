"""Shared pytest fixtures for the Flask application."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture
def app() -> Flask:
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "LOGIN_RATE_LIMITER": lambda _url, _subject: True,
            "LOGIN_RATE_LIMIT_RESETTER": lambda _url, _subject: None,
        }
    )


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
