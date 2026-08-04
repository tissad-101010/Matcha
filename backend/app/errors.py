"""Central JSON error responses without internal implementation details."""

from typing import Any

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def _error_payload(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: Flask) -> None:
    """Register consistent handlers for expected and unexpected errors."""

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):  # type: ignore[no-untyped-def]
        code = error.name.lower().replace(" ", "_")
        return jsonify(_error_payload(code, error.description)), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):  # type: ignore[no-untyped-def]
        app.logger.exception("Unhandled request error", exc_info=error)
        return jsonify(_error_payload("internal_error", "Une erreur interne est survenue.")), 500
