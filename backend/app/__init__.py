"""Application factory for the Matcha backend."""

from flask import Flask

from app.config import build_config
from app.errors import register_error_handlers
from app.extensions import init_extensions
from app.routes.auth import auth_blueprint, csrf_blueprint
from app.routes.discovery import discovery_blueprint
from app.routes.health import health_blueprint
from app.routes.location import location_blueprint
from app.routes.photos import photos_blueprint
from app.routes.profile import profile_blueprint
from app.routes.search import search_blueprint
from app.routes.tags import tags_blueprint


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    """Create an isolated Flask application for production or tests."""
    app = Flask(__name__)
    app.config.from_mapping(build_config())

    if test_config:
        app.config.update(test_config)

    init_extensions(app)
    register_error_handlers(app)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(csrf_blueprint)
    app.register_blueprint(health_blueprint)
    app.register_blueprint(discovery_blueprint)
    app.register_blueprint(location_blueprint)
    app.register_blueprint(photos_blueprint)
    app.register_blueprint(profile_blueprint)
    app.register_blueprint(search_blueprint)
    app.register_blueprint(tags_blueprint)

    return app
