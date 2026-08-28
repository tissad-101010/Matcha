"""Business rules for blocking and reporting."""

import pytest

from app.interactions.service import InteractionError
from app.moderation.service import block_profile, report_profile, unblock_profile


def test_self_moderation_actions_are_refused() -> None:
    with pytest.raises(InteractionError) as blocked:
        block_profile("database", "same", "same")
    with pytest.raises(InteractionError) as reported:
        report_profile("database", "same", "same", "spam", None)
    assert blocked.value.code == "self_interaction"
    assert reported.value.code == "self_interaction"


def test_unblock_does_not_restore_relationship(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "app.moderation.service.remove_block",
        lambda database_url, actor_id, target_id: calls.append(
            (database_url, actor_id, target_id)
        )
        or True,
    )
    unblock_profile("database", "actor", "target")
    assert calls == [("database", "actor", "target")]
