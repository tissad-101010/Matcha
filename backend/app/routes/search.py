"""Authenticated advanced profile search."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth
from app.auth.validation import InputValidationError
from app.discovery.service import DiscoveryUnavailableError, suggestions
from app.discovery.validation import validate_search_query

search_blueprint = Blueprint("search", __name__, url_prefix="/api/v1/search")


@search_blueprint.get("/profiles")
@require_auth
def search_profiles():  # type: ignore[no-untyped-def]
    """Combine public criteria while retaining all discovery exclusions."""
    try:
        query = validate_search_query(request.args, request.args.getlist("tag_ids"))
        result = suggestions(
            str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "", query
        )
    except InputValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Critères de recherche invalides.",
                    "fields": error.fields,
                }
            }
        ), 422
    except DiscoveryUnavailableError:
        return jsonify(
            {
                "error": {
                    "code": "profile_incomplete",
                    "message": "Complétez votre profil avant la recherche.",
                }
            }
        ), 403
    return jsonify(result)
