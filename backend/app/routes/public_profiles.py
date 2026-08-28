"""Authorized public profile reads without visit side effects."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify

from app.auth.session_access import authenticated_user_id, require_auth
from app.profile.repository import get_public_profile

public_profiles_blueprint = Blueprint("public_profiles", __name__, url_prefix="/api/v1/profiles")


@public_profiles_blueprint.get("/<uuid:target_id>")
@require_auth
def read_public_profile(target_id: UUID):  # type: ignore[no-untyped-def]
    profile = get_public_profile(
        str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "", target_id
    )
    if profile is None:
        return jsonify({"error": {"code": "not_found", "message": "Profil introuvable."}}), 404
    return jsonify({"data": profile})
