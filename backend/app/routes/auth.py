"""HTTP endpoints for account registration and authentication."""

import hmac
import secrets
from datetime import UTC, datetime

from flask import Blueprint, current_app, jsonify, request, session

from app.auth.rate_limit import clear_login_limit, login_allowed
from app.auth.repository import DuplicateAccountError, InvalidTokenError
from app.auth.service import InvalidCredentialsError, authenticate, register, verify_email
from app.auth.validation import (
    InputValidationError,
    validate_login,
    validate_register,
    validate_token,
)

auth_blueprint = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
csrf_blueprint = Blueprint("csrf", __name__, url_prefix="/api/v1")


@auth_blueprint.post("/register")
def register_account():  # type: ignore[no-untyped-def]
    """Validate a registration and create an unverified account."""
    try:
        data = validate_register(request.get_json(silent=True))
        result = register(current_app.config, data)
    except InputValidationError as error:
        return _error("validation_error", "Certains champs sont invalides.", 422, error.fields)
    except DuplicateAccountError as error:
        return _error(
            "account_conflict",
            "Cette adresse e-mail ou ce nom d’utilisateur est indisponible.",
            409,
            {error.field: "Cette valeur est déjà utilisée."},
        )

    return (
        jsonify(
            {
                "data": {
                    "account_id": str(result.account_id),
                    "status": "pending_verification",
                    "verification_email_sent": result.verification_email_sent,
                }
            }
        ),
        201,
    )


@auth_blueprint.post("/verify-email")
def verify_account_email():  # type: ignore[no-untyped-def]
    """Consume an e-mail verification token and activate its account."""
    try:
        token = validate_token(request.get_json(silent=True))
        account = verify_email(current_app.config, token)
    except (InputValidationError, InvalidTokenError):
        return _error(
            "invalid_token",
            "Ce lien d’activation est invalide ou expiré.",
            422,
            {"token": "Demandez un nouveau lien d’activation."},
        )

    return jsonify(
        {
            "data": {
                "id": str(account.account_id),
                "username": account.username,
                "first_name": account.first_name,
                "account_status": "active",
                "profile_complete": False,
                "has_main_photo": False,
                "matching_enabled": False,
            }
        }
    )


@csrf_blueprint.get("/csrf")
def csrf_token():  # type: ignore[no-untyped-def]
    """Create or return the CSRF token bound to the current server-side session."""
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return jsonify({"data": {"csrf_token": session["csrf_token"]}})


@auth_blueprint.post("/login")
def login():  # type: ignore[no-untyped-def]
    """Create a rotated server-side session for valid active credentials."""
    try:
        data = validate_login(request.get_json(silent=True))
        subject = f"{request.remote_addr or 'unknown'}:{data.username}"
        limiter = current_app.config.get("LOGIN_RATE_LIMITER", login_allowed)
        if not limiter(str(current_app.config["VALKEY_URL"]), subject):
            return _error("rate_limited", "Trop de tentatives. Réessayez plus tard.", 429, {})
        account = authenticate(current_app.config, data.username, data.password)
    except (InputValidationError, InvalidCredentialsError):
        return _error(
            "invalid_credentials", "Nom d’utilisateur ou mot de passe incorrect.", 401, {}
        )

    resetter = current_app.config.get("LOGIN_RATE_LIMIT_RESETTER", clear_login_limit)
    resetter(str(current_app.config["VALKEY_URL"]), subject)

    session.clear()
    session["user_id"] = str(account.account_id)
    session["csrf_token"] = secrets.token_urlsafe(32)
    session["user"] = _session_user(account)
    session.permanent = True
    current_app.session_interface.regenerate(session)  # type: ignore[attr-defined]
    return jsonify({"data": _session_response(account)})


@auth_blueprint.get("/session")
def current_session():  # type: ignore[no-untyped-def]
    """Return the current authenticated session without exposing its opaque id."""
    if "user_id" not in session:
        return _error("authentication_required", "Authentification requise.", 401, {})
    expires_at = datetime.now(UTC) + current_app.permanent_session_lifetime
    return jsonify(
        {
            "data": {
                "user": session["user"],
                "csrf_token": session["csrf_token"],
                "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            }
        }
    )


@auth_blueprint.post("/logout")
def logout():  # type: ignore[no-untyped-def]
    """Revoke the current server-side session after CSRF verification."""
    expected = session.get("csrf_token", "")
    supplied = request.headers.get("X-CSRF-Token", "")
    if "user_id" not in session:
        return _error("authentication_required", "Authentification requise.", 401, {})
    if not expected or not hmac.compare_digest(expected, supplied):
        return _error("csrf_failed", "Jeton CSRF invalide.", 403, {})
    session.clear()
    return "", 204


def _session_response(account):  # type: ignore[no-untyped-def]
    expires_at = datetime.now(UTC) + current_app.permanent_session_lifetime
    return {
        "user": _session_user(account),
        "csrf_token": session["csrf_token"],
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }


def _session_user(account):  # type: ignore[no-untyped-def]
    return {
        "id": str(account.account_id),
        "username": account.username,
        "first_name": account.first_name,
        "account_status": account.status,
        "profile_complete": account.profile_complete,
        "has_main_photo": account.has_main_photo,
        "matching_enabled": account.matching_enabled,
    }


def _error(code: str, message: str, status: int, fields: dict[str, str]):  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": code, "message": message, "fields": fields}}), status
