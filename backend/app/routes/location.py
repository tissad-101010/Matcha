"""Authenticated location endpoints with explicit GPS privacy boundaries."""

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.auth.validation import InputValidationError
from app.location.repository import (
    UnknownLocationError,
    delete_location,
    save_location,
    search_locations,
)
from app.location.service import UnsupportedGpsAreaError, save_reduced_gps
from app.location.validation import (
    validate_gps_location,
    validate_location_query,
    validate_manual_location,
)
from app.profile.repository import location_consent_active
from app.profile.service import private_profile

location_blueprint = Blueprint("location", __name__, url_prefix="/api/v1")


@location_blueprint.get("/locations")
@require_auth
def list_locations():  # type: ignore[no-untyped-def]
    """Search the local catalogue without any third-party request."""
    try:
        query, limit = validate_location_query(request.args.get("query"), request.args.get("limit"))
    except InputValidationError as error:
        return _validation_error(error)
    locations = search_locations(str(current_app.config["DATABASE_URL"]), query, limit)
    return jsonify({"data": locations, "meta": {"count": len(locations)}})


@location_blueprint.get("/me/location")
@require_auth
def read_location():  # type: ignore[no-untyped-def]
    """Return only the current member's approximate private location."""
    profile = private_profile(
        str(current_app.config["DATABASE_URL"]), authenticated_user_id() or ""
    )
    return jsonify({"data": profile["location"] if profile else None})


@location_blueprint.put("/me/location/manual")
@require_csrf
def set_manual_location():  # type: ignore[no-untyped-def]
    """Store a user-selected offline catalogue location without GPS consent."""
    try:
        catalog_id = validate_manual_location(request.get_json(silent=True))
        location = save_location(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            catalog_id,
            "manual",
        )
    except InputValidationError as error:
        return _validation_error(error)
    except UnknownLocationError:
        return _unknown_location()
    return jsonify({"data": location})


@location_blueprint.put("/me/location/gps")
@require_csrf
def set_gps_location():  # type: ignore[no-untyped-def]
    """Reduce transient GPS coordinates only after specific active consent."""
    try:
        latitude, longitude = validate_gps_location(request.get_json(silent=True))
    except InputValidationError as error:
        return _validation_error(error)
    database_url = str(current_app.config["DATABASE_URL"])
    user_id = authenticated_user_id() or ""
    if not location_consent_active(database_url, user_id):
        return jsonify(
            {"error": {"code": "consent_required", "message": "Consentement GPS requis."}}
        ), 403
    try:
        location = save_reduced_gps(database_url, user_id, latitude, longitude)
    except UnsupportedGpsAreaError:
        return jsonify(
            {
                "error": {
                    "code": "location_not_supported",
                    "message": "Choisissez une ville dans le catalogue local.",
                }
            }
        ), 422
    return jsonify({"data": location})


@location_blueprint.delete("/me/location")
@require_csrf
def remove_location():  # type: ignore[no-untyped-def]
    """Erase the current location so another source can replace it."""
    delete_location(str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "")
    return "", 204


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


def _unknown_location():  # type: ignore[no-untyped-def]
    return jsonify(
        {
            "error": {
                "code": "unknown_location",
                "message": "Cette localisation n’existe plus.",
                "fields": {"catalog_location_id": "Actualisez les propositions."},
            }
        }
    ), 422
