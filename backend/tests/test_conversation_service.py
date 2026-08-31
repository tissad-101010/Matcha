"""Conversation hide behavior remains local and authorization-safe."""

from uuid import UUID

import pytest

from app.conversations.service import hide_conversation, send_message
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
    monkeypatch.setattr("app.conversations.service.hide_for_member", lambda *_args: False)
    with pytest.raises(InteractionError) as raised:
        hide_conversation("database", "outsider", CONVERSATION_ID)
    assert raised.value.code == "not_found"


def test_send_message_normalizes_and_persists(monkeypatch) -> None:
    message_id = UUID("00000000-0000-4000-8000-000000000051")
    expected = {"id": str(message_id)}
    calls = []
    monkeypatch.setattr(
        "app.conversations.service.insert_message",
        lambda *args: calls.append(args) or expected,
    )
    result = send_message(
        "database",
        "member-a",
        CONVERSATION_ID,
        UUID("e3fa8774-5162-4b31-a8d6-aef88210c059"),
        "  Bonjour !  ",
    )
    assert result == expected
    assert calls[0][-1] == "Bonjour !"


@pytest.mark.parametrize(
    ("client_id", "body"),
    [
        (UUID("00000000-0000-1000-8000-000000000052"), "bonjour"),
        (UUID("e3fa8774-5162-4b31-a8d6-aef88210c059"), "   "),
        (UUID("e3fa8774-5162-4b31-a8d6-aef88210c059"), "x" * 2001),
    ],
)
def test_send_message_rejects_invalid_input(client_id: UUID, body: str) -> None:
    with pytest.raises(InteractionError) as raised:
        send_message("database", "member-a", CONVERSATION_ID, client_id, body)
    assert raised.value.code == "validation_error"


def test_send_message_hides_conversation_authorization_result(monkeypatch) -> None:
    monkeypatch.setattr("app.conversations.service.insert_message", lambda *_args: None)
    with pytest.raises(InteractionError) as raised:
        send_message(
            "database",
            "outsider",
            CONVERSATION_ID,
            UUID("e3fa8774-5162-4b31-a8d6-aef88210c059"),
            "bonjour",
        )
    assert raised.value.code == "not_found"
