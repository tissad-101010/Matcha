"""Authenticated notification center endpoints."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth, require_csrf
from app.interactions.service import InteractionError
from app.notifications.repository import list_for_recipient, unread_count
from app.notifications.service import read_all, read_one

notifications_blueprint = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")


@notifications_blueprint.get("")
@require_auth
def list_notifications():  # type: ignore[no-untyped-def]
    try:
        limit = int(request.args.get("limit", "20"))
        if limit < 1 or limit > 100:
            raise ValueError
        raw_before = request.args.get("before")
        before = UUID(raw_before) if raw_before else None
    except (ValueError, AttributeError):
        return _validation_error()
    data = list_for_recipient(
        str(current_app.config["DATABASE_URL"]),
        authenticated_user_id() or "",
        before,
        limit,
    )
    return jsonify({"data": data, "meta": {"count": len(data), "limit": limit}})


@notifications_blueprint.get("/unread-count")
@require_auth
def get_unread_count():  # type: ignore[no-untyped-def]
    count = unread_count(str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "")
    return jsonify({"data": {"unread_count": count}})


@notifications_blueprint.post("/<uuid:notification_id>/read")
@require_csrf
def mark_notification_read(notification_id: UUID):  # type: ignore[no-untyped-def]
    try:
        read_one(
            str(current_app.config["DATABASE_URL"]),
            authenticated_user_id() or "",
            notification_id,
        )
    except InteractionError as error:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status
    return "", 204


@notifications_blueprint.post("/read-all")
@require_csrf
def mark_all_notifications_read():  # type: ignore[no-untyped-def]
    count = read_all(str(current_app.config["DATABASE_URL"]), authenticated_user_id() or "")
    return jsonify({"data": {"updated_count": count}})


def _validation_error():  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": "validation_error", "message": "Pagination invalide."}}), 422
