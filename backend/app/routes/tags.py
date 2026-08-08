"""Authenticated endpoints for reusable tags and profile selections."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.auth.validation import InputValidationError
from app.profile.service import private_profile
from app.tags.repository import (
    DuplicateTagError,
    UnknownTagError,
    create_tag,
    replace_profile_tags,
    search_tags,
)
from app.tags.validation import validate_new_tag, validate_tag_ids, validate_tag_query

tags_blueprint = Blueprint("tags", __name__, url_prefix="/api/v1")


@tags_blueprint.get("/tags")
@require_auth
def list_tags():  # type: ignore[no-untyped-def]
    """Search the shared catalogue without exposing creator information."""
    try:
        query, limit = validate_tag_query(request.args.get("query"), request.args.get("limit"))
    except InputValidationError as error:
        return _validation_error(error)
    tags = search_tags(str(current_app.config["DATABASE_URL"]), query, limit)
    return jsonify({"data": tags, "meta": {"count": len(tags)}})


@tags_blueprint.post("/tags")
@require_csrf
def add_tag():  # type: ignore[no-untyped-def]
    """Create a normalized catalogue entry for future reuse."""
    try:
        name, normalized = validate_new_tag(request.get_json(silent=True))
        tag = create_tag(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            name,
            normalized,
        )
    except InputValidationError as error:
        return _validation_error(error)
    except DuplicateTagError:
        return jsonify(
            {
                "error": {
                    "code": "tag_conflict",
                    "message": "Ce tag existe déjà.",
                    "fields": {"name": "Choisissez le tag existant."},
                }
            }
        ), 409
    return jsonify({"data": tag}), 201


@tags_blueprint.put("/me/tags")
@require_csrf
def edit_profile_tags():  # type: ignore[no-untyped-def]
    """Replace the current member's selected tags and return the fresh profile."""
    try:
        tag_ids = validate_tag_ids(request.get_json(silent=True))
        database_url = str(current_app.config["DATABASE_URL"])
        user_id = authenticated_user_id() or ""
        replace_profile_tags(database_url, user_id, tag_ids)
    except InputValidationError as error:
        return _validation_error(error)
    except UnknownTagError:
        return jsonify(
            {
                "error": {
                    "code": "unknown_tag",
                    "message": "Un tag sélectionné n’existe plus.",
                    "fields": {"tag_ids": "Actualisez la liste des tags."},
                }
            }
        ), 422
    return jsonify({"data": private_profile(database_url, user_id)})


def _validation_error(error: InputValidationError):  # type: ignore[no-untyped-def]
    return jsonify(
        {
            "error": {
                "code": "validation_error",
                "message": "Certains champs sont invalides.",
                "fields": error.fields,
            }
        }
    ), 422
