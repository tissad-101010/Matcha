"""Conversation hide behavior remains local and authorization-safe."""

from uuid import UUID

import pytest

from app.conversations.service import hide_conversation
from app.interactions.service import InteractionError

CONVERSATION_ID = UUID("00000000-0000-4000-8000-000000000050")


def test_hide_delegates_only_the_current_member(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "app.conversations.service.hide_for_member",
        lambda *args: calls.append(args) or True,
    )
    hide_conversation("database", "member-a", CONVERSATION_ID)
    assert calls == [("database", "member-a", CONVERSATION_ID)]


def test_hide_refuses_non_member_without_disclosing_existence(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.conversations.service.hide_for_member", lambda *_args: False
    )
    with pytest.raises(InteractionError) as raised:
        hide_conversation("database", "outsider", CONVERSATION_ID)
    assert raised.value.code == "not_found"
