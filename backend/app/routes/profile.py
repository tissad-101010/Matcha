"""Authenticated private profile endpoints used by onboarding."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.auth.validation import InputValidationError
from app.profile.repository import update_profile
from app.profile.service import private_profile
from app.profile.validation import validate_profile_update

profile_blueprint = Blueprint("profile", __name__, url_prefix="/api/v1/me")


@profile_blueprint.get("/profile")
@require_auth
def read_private_profile():  # type: ignore[no-untyped-def]
    """Return the complete private onboarding aggregate for the current member."""
    profile = private_profile(
        str(current_app.config["DATABASE_URL"]), authenticated_user_id() or ""
    )
    if profile is None:
        return jsonify({"error": {"code": "not_found", "message": "Profil introuvable."}}), 404
    return jsonify({"data": profile})


@profile_blueprint.patch("/profile")
@require_csrf
def edit_private_profile():  # type: ignore[no-untyped-def]
    """Update allowlisted identity fields, then return the fresh aggregate."""
    try:
        changes = validate_profile_update(request.get_json(silent=True))
    except InputValidationError as error:
        payload = {
            "error": {
                "code": "validation_error",
                "message": "Certains champs sont invalides.",
                "fields": error.fields,
            }
        }
        return jsonify(payload), 422
    user_id = authenticated_user_id() or ""
    database_url = str(current_app.config["DATABASE_URL"])
    update_profile(database_url, user_id, changes)
    return jsonify({"data": private_profile(database_url, user_id)})
