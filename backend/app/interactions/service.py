"""Business rules for likes and matches."""

from dataclasses import dataclass

from app.interactions.repository import deactivate_pair, insert_visit, upsert_like_and_match


@dataclass(frozen=True)
class InteractionError(Exception):
    """Expected interaction refusal exposed as a stable API error."""

    code: str
    message: str
    status: int


def like_profile(database_url: str, source_id: str, target_id: str) -> dict[str, object]:
    """Create an idempotent like and an atomic match when it is reciprocal."""
    if source_id == target_id:
        raise InteractionError("self_interaction", "Vous ne pouvez pas liker votre profil.", 422)
    result = upsert_like_and_match(database_url, source_id, target_id)
    if result == "not_found":
        raise InteractionError("not_found", "Profil introuvable.", 404)
    if result == "blocked":
        raise InteractionError("interaction_forbidden", "Cette interaction est indisponible.", 403)
    if result == "photo_required":
        raise InteractionError(
            "main_photo_required", "Ajoutez une photo principale avant de liker un profil.", 403
        )
    return result


def unlike_profile(database_url: str, source_id: str, target_id: str) -> dict[str, object]:
    """Deactivate both likes and end the active match for a disconnected pair."""
    if source_id == target_id:
        raise InteractionError("self_interaction", "Interaction invalide.", 422)
    result = deactivate_pair(database_url, source_id, target_id)
    if result is None:
        raise InteractionError("not_found", "Like actif introuvable.", 404)
    return result


def record_profile_visit(database_url: str, visitor_id: str, visited_id: str) -> None:
    """Record only explicit visits between distinct, authorized users."""
    if visitor_id == visited_id:
        raise InteractionError("self_interaction", "Votre propre profil n'est pas une visite.", 422)
    if not insert_visit(database_url, visitor_id, visited_id):
        raise InteractionError("not_found", "Profil introuvable.", 404)
