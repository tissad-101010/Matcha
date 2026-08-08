"""Authenticated private profile endpoints used by onboarding."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.auth.validation import InputValidationError
from app.profile.repository import (
    matching_consent_active,
    record_matching_consent,
    replace_preferences,
    update_profile,
)
from app.profile.service import private_profile
from app.profile.validation import (
    validate_consent,
    validate_preferences,
    validate_profile_update,
)

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


@profile_blueprint.put("/preferences")
@require_csrf
def edit_preferences():  # type: ignore[no-untyped-def]
    """Replace desired genders only after explicit sensitive-data consent."""
    try:
        genders = validate_preferences(request.get_json(silent=True))
    except InputValidationError as error:
        return _validation_error(error)
    user_id = authenticated_user_id() or ""
    database_url = str(current_app.config["DATABASE_URL"])
    if not matching_consent_active(database_url, user_id):
        return jsonify(
            {"error": {"code": "consent_required", "message": "Consentement requis."}}
        ), 403
    replace_preferences(database_url, user_id, genders)
    return jsonify({"data": private_profile(database_url, user_id)})


@profile_blueprint.delete("/preferences")
@require_csrf
def clear_preferences():  # type: ignore[no-untyped-def]
    """Clear explicit choices; active consent then means all genders."""
    user_id = authenticated_user_id() or ""
    database_url = str(current_app.config["DATABASE_URL"])
    replace_preferences(database_url, user_id, [])
    return "", 204


@profile_blueprint.get("/consents")
@require_auth
def read_consents():  # type: ignore[no-untyped-def]
    """Return latest auditable consent states from the private aggregate."""
    profile = private_profile(
        str(current_app.config["DATABASE_URL"]), authenticated_user_id() or ""
    )
    return jsonify({"data": profile["consents"] if profile else []})


@profile_blueprint.put("/consents/preferences")
@require_csrf
def grant_preferences_consent():  # type: ignore[no-untyped-def]
    """Record explicit consent separately from the preference values."""
    version = str(current_app.config["CONSENT_POLICY_VERSION"])
    try:
        validate_consent(request.get_json(silent=True), version)
    except InputValidationError as error:
        return _validation_error(error)
    record_matching_consent(
        str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "", version, True
    )
    return "", 204


@profile_blueprint.delete("/consents/preferences")
@require_csrf
def withdraw_preferences_consent():  # type: ignore[no-untyped-def]
    """Withdraw consent and erase stored preferences in the same transaction."""
    record_matching_consent(
        str(current_app.config["DATABASE_URL"]),
        authenticated_user_id() or "",
        str(current_app.config["CONSENT_POLICY_VERSION"]),
        False,
    )
    return "", 204


def _validation_error(error: InputValidationError):  # type: ignore[no-untyped-def]
    payload = {
        "error": {
            "code": "validation_error",
            "message": "Certains champs sont invalides.",
            "fields": error.fields,
        }
    }
    return jsonify(payload), 422
