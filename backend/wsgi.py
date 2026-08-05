"""Gunicorn entrypoint exposing the Flask application."""

from app import create_app

app = create_app()
