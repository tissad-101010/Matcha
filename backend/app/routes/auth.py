"""HTTP endpoints for account registration and authentication."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.repository import DuplicateAccountError, InvalidTokenError
from app.auth.service import register, verify_email
from app.auth.validation import InputValidationError, validate_register, validate_token

auth_blueprint = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


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


def _error(code: str, message: str, status: int, fields: dict[str, str]):  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": code, "message": message, "fields": fields}}), status
