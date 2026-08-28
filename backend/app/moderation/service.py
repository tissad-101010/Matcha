"""Business rules for blocking and reporting profiles."""

from app.interactions.service import InteractionError
from app.moderation.repository import create_block, create_report, remove_block


def block_profile(database_url: str, actor_id: str, target_id: str):  # type: ignore[no-untyped-def]
    if actor_id == target_id:
        raise InteractionError("self_interaction", "Vous ne pouvez pas vous bloquer.", 422)
    result = create_block(database_url, actor_id, target_id)
    if result is None:
        raise InteractionError("not_found", "Profil introuvable.", 404)
    return result


def unblock_profile(database_url: str, actor_id: str, target_id: str) -> None:
    if not remove_block(database_url, actor_id, target_id):
        raise InteractionError("not_found", "Blocage introuvable.", 404)


def report_profile(
    database_url: str,
    actor_id: str,
    target_id: str,
    reason: str,
    description: str | None,
):
    if actor_id == target_id:
        raise InteractionError("self_interaction", "Vous ne pouvez pas vous signaler.", 422)
    result = create_report(database_url, actor_id, target_id, reason, description)
    if result is None:
        raise InteractionError("not_found", "Profil introuvable.", 404)
    return result
