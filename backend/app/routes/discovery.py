"""Authenticated profile suggestion endpoints."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth
from app.auth.validation import InputValidationError
from app.discovery.service import DiscoveryUnavailableError, suggestions
from app.discovery.validation import validate_discovery_query

discovery_blueprint = Blueprint("discovery", __name__, url_prefix="/api/v1/discovery")


@discovery_blueprint.get("/suggestions")
@require_auth
def list_suggestions():  # type: ignore[no-untyped-def]
    try:
        query = validate_discovery_query(request.args.get("cursor"), request.args.get("limit"))
        result = suggestions(
            str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "", query
        )
    except InputValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Filtres invalides.",
                    "fields": error.fields,
                }
            }
        ), 422
    except DiscoveryUnavailableError:
        return jsonify(
            {
                "error": {
                    "code": "profile_incomplete",
                    "message": "Complétez votre profil avant la découverte.",
                }
            }
        ), 403
    return jsonify(result)
