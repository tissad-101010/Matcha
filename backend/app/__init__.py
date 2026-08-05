"""Application factory for the Matcha backend."""

from flask import Flask

from app.config import build_config
from app.errors import register_error_handlers
from app.extensions import init_extensions
from app.routes.auth import auth_blueprint
from app.routes.health import health_blueprint


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    """Create an isolated Flask application for production or tests."""
    app = Flask(__name__)
    app.config.from_mapping(build_config())

    if test_config:
        app.config.update(test_config)

    init_extensions(app)
    register_error_handlers(app)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(health_blueprint)

    return app
