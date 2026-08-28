"""Authenticated and CSRF-protected profile interactions."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify

from app.auth.session_access import authenticated_user_id, require_csrf
from app.interactions.service import InteractionError, like_profile, unlike_profile

interactions_blueprint = Blueprint("interactions", __name__, url_prefix="/api/v1/profiles")


def _run(action, target_id: UUID):  # type: ignore[no-untyped-def]
    try:
        result = action(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            str(target_id),
        )
    except InteractionError as error:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return jsonify({"data": result})


@interactions_blueprint.post("/<uuid:target_id>/like")
@require_csrf
def create_like(target_id: UUID):  # type: ignore[no-untyped-def]
    return _run(like_profile, target_id)


@interactions_blueprint.delete("/<uuid:target_id>/like")
@require_csrf
def delete_like(target_id: UUID):  # type: ignore[no-untyped-def]
    return _run(unlike_profile, target_id)
