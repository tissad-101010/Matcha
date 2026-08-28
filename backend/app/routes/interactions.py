"""Authenticated and CSRF-protected profile interactions."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_csrf
from app.auth.validation import InputValidationError
from app.interactions.service import (
    InteractionError,
    like_profile,
    record_profile_visit,
    unlike_profile,
)
from app.moderation.service import block_profile, report_profile, unblock_profile
from app.moderation.validation import validate_report

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


@interactions_blueprint.post("/<uuid:target_id>/visit")
@require_csrf
def create_profile_visit(target_id: UUID):  # type: ignore[no-untyped-def]
    try:
        record_profile_visit(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            str(target_id),
        )
    except InteractionError as error:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return "", 204


@interactions_blueprint.post("/<uuid:target_id>/block")
@require_csrf
def create_profile_block(target_id: UUID):  # type: ignore[no-untyped-def]
    return _run(block_profile, target_id)


@interactions_blueprint.delete("/<uuid:target_id>/block")
@require_csrf
def delete_profile_block(target_id: UUID):  # type: ignore[no-untyped-def]
    try:
        unblock_profile(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            str(target_id),
        )
    except InteractionError as error:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return "", 204


@interactions_blueprint.post("/<uuid:target_id>/reports")
@require_csrf
def create_profile_report(target_id: UUID):  # type: ignore[no-untyped-def]
    try:
        reason, description = validate_report(request.get_json(silent=True))
        result = report_profile(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            str(target_id),
            reason,
            description,
        )
    except InputValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Signalement invalide.",
                    "fields": error.fields,
                }
            }
        ), 422
    except InteractionError as error:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return jsonify({"data": result}), 201
