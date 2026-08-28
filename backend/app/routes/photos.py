"""Authenticated HTTP endpoints for mandatory private profile photos."""

from flask import Blueprint, current_app, jsonify, request, send_file

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.auth.validation import InputValidationError
from app.photos.image_processing import InvalidImageError
from app.photos.repository import (
    PhotoLimitError,
    PhotoNotFoundError,
    find_accessible_photo,
    list_photos,
    update_photo,
)
from app.photos.service import add_profile_photo, delete_profile_photo, photo_summary
from app.photos.storage import photo_client, read_photo
from app.photos.validation import validate_photo_id, validate_photo_update

photos_blueprint = Blueprint("photos", __name__, url_prefix="/api/v1")


@photos_blueprint.get("/me/photos")
@require_auth
def own_photos():  # type: ignore[no-untyped-def]
    photos = list_photos(str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "")
    return jsonify({"data": [photo_summary(photo) for photo in photos]})


@photos_blueprint.post("/me/photos")
@require_csrf
def upload_photo():  # type: ignore[no-untyped-def]
    uploaded = request.files.get("file")
    if uploaded is None:
        return _validation_error({"file": "Une image est requise."})
    try:
        photo = add_profile_photo(
            current_app.config, authenticated_user_id() or "", uploaded.stream.read()
        )
    except InvalidImageError as error:
        return _validation_error({"file": str(error)})
    except PhotoLimitError:
        return jsonify({"error": {"code": "photo_limit", "message": "Cinq photos maximum."}}), 409
    return jsonify({"data": photo}), 201


@photos_blueprint.patch("/me/photos/<photo_id>")
@require_csrf
def edit_photo(photo_id: str):  # type: ignore[no-untyped-def]
    try:
        parsed_id = validate_photo_id(photo_id)
        position, is_main = validate_photo_update(request.get_json(silent=True))
        photos = update_photo(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            parsed_id,
            position,
            is_main,
        )
    except InputValidationError as error:
        return _validation_error(error.fields)
    except ValueError:
        return _validation_error({"position": "Cette position n’existe pas."})
    except PhotoNotFoundError:
        return _not_found()
    return jsonify({"data": [photo_summary(photo) for photo in photos]})


@photos_blueprint.delete("/me/photos/<photo_id>")
@require_csrf
def remove_own_photo(photo_id: str):  # type: ignore[no-untyped-def]
    try:
        delete_profile_photo(
            current_app.config,
            authenticated_user_id() or "",
            validate_photo_id(photo_id),
        )
    except InputValidationError as error:
        return _validation_error(error.fields)
    except PhotoNotFoundError:
        return _not_found()
    return "", 204


@photos_blueprint.get("/photos/<photo_id>")
@require_auth
def serve_photo(photo_id: str):  # type: ignore[no-untyped-def]
    try:
        photo = find_accessible_photo(
            str(current_app.config["DATABASE_URL"]),
            validate_photo_id(photo_id),
            authenticated_user_id() or "",
        )
    except (InputValidationError, PhotoNotFoundError):
        return _not_found()
    content = read_photo(photo_client(current_app.config), photo.object_key)
    return send_file(content, mimetype="image/webp", max_age=0)


def _validation_error(fields: dict[str, str]):  # type: ignore[no-untyped-def]
    return jsonify(
        {"error": {"code": "validation_error", "message": "Image invalide.", "fields": fields}}
    ), 422


def _not_found():  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": "not_found", "message": "Photo introuvable."}}), 404
