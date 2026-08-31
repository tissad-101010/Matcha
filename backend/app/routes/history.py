"""Authenticated personal visit and received-like histories."""

from uuid import UUID

from flask import Blueprint, current_app, jsonify, request

from app.auth.session_access import authenticated_user_id, require_auth
from app.history.repository import likes_received, visitors

history_blueprint = Blueprint("history", __name__, url_prefix="/api/v1/me")


@history_blueprint.get("/visitors")
@require_auth
def list_visitors():  # type: ignore[no-untyped-def]
    parsed = _pagination(with_period=True)
    if parsed is None:
        return _error()
    before, limit, period = parsed
    data = visitors(
        str(current_app.config["DATABASE_URL"]),
        authenticated_user_id() or "",
        before,
        limit,
        period,
    )
    return jsonify({"data": data, "meta": {"count": len(data), "limit": limit}})


@history_blueprint.get("/likes-received")
@require_auth
def list_likes_received():  # type: ignore[no-untyped-def]
    parsed = _pagination(with_period=False)
    if parsed is None:
        return _error()
    before, limit, _period = parsed
    data = likes_received(
        str(current_app.config["DATABASE_URL"]),
        authenticated_user_id() or "",
        before,
        limit,
    )
    return jsonify({"data": data, "meta": {"count": len(data), "limit": limit}})


def _pagination(with_period: bool) -> tuple[UUID | None, int, int | None] | None:
    try:
        limit = int(request.args.get("limit", "20"))
        if limit < 1 or limit > 100:
            raise ValueError
        raw_before = request.args.get("before")
        before = UUID(raw_before) if raw_before else None
        raw_period = request.args.get("period", "30") if with_period else "all"
        if raw_period not in {"7", "30", "90", "all"}:
            raise ValueError
        period = None if raw_period == "all" else int(raw_period)
    except (ValueError, AttributeError):
        return None
    return before, limit, period


def _error():  # type: ignore[no-untyped-def]
    return jsonify({"error": {"code": "validation_error", "message": "Pagination invalide."}}), 422
