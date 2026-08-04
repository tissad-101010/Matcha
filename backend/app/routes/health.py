"""Process health endpoints used by local tools and containers."""

from flask import Blueprint, jsonify

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health/live")
def live():
    """Confirm that the Flask process can handle HTTP requests."""
    return jsonify({"data": {"status": "ok"}})
