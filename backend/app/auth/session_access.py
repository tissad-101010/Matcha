"""Reusable authorization and CSRF guards for authenticated endpoints."""

import hmac
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import current_app, jsonify, request, session

from app.auth.repository import session_is_current


def authenticated_user_id() -> str | None:
    """Return a current active user id or revoke a stale session."""
    user_id = session.get("user_id")
    auth_version = session.get("auth_version")
    if not isinstance(user_id, str) or not isinstance(auth_version, int):
        return None
    validator = current_app.config.get("SESSION_VALIDATOR", session_is_current)
    if not validator(str(current_app.config["DATABASE_URL"]), user_id, auth_version):
        session.clear()
        return None
    return user_id


def require_auth(view: Callable[..., Any]) -> Callable[..., Any]:
    """Protect a route with the current server-side session."""
    @wraps(view)
    def protected(*args: Any, **kwargs: Any) -> Any:
        if authenticated_user_id() is None:
            payload = {
                "error": {
                    "code": "authentication_required",
                    "message": "Authentification requise.",
                }
            }
            return jsonify(payload), 401
        return view(*args, **kwargs)

    return protected


def require_csrf(view: Callable[..., Any]) -> Callable[..., Any]:
    """Protect a mutation with the token bound to its server-side session."""
    @wraps(view)
    @require_auth
    def protected(*args: Any, **kwargs: Any) -> Any:
        expected = session.get("csrf_token", "")
        supplied = request.headers.get("X-CSRF-Token", "")
        if not expected or not hmac.compare_digest(expected, supplied):
            payload = {"error": {"code": "csrf_failed", "message": "Jeton CSRF invalide."}}
            return jsonify(payload), 403
        return view(*args, **kwargs)

    return protected
