"""Process health endpoints used by local tools and containers."""

from flask import Blueprint, current_app, jsonify

from app.infrastructure import check_dependencies

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health/live")
def live():
    """Confirm that the Flask process can handle HTTP requests."""
    return jsonify({"data": {"status": "ok"}})


@health_blueprint.get("/health/ready")
def ready():
    """Confirm that every mandatory backend dependency is usable."""
    checker = current_app.config.get("READINESS_CHECK", check_dependencies)
    checks = checker(current_app.config)
    ready_state = all(checks.values())
    status_code = 200 if ready_state else 503
    status = "ready" if ready_state else "unavailable"
    return jsonify({"data": {"status": status, "checks": checks}}), status_code
