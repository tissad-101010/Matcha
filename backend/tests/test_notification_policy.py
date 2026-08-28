"""Directional notification policy after an unlike."""

from unittest.mock import MagicMock

from app.interactions.repository import notifications_allowed


def connection_returning(row):  # type: ignore[no-untyped-def]
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = row
    return connection


def test_user_who_unliked_suppresses_events_from_the_old_match() -> None:
    connection = connection_returning(("ended_unlike", "user-a"))
    assert not notifications_allowed(connection, "user-a", "user-b")


def test_direction_remains_open_for_the_user_who_unliked() -> None:
    connection = connection_returning(("ended_unlike", "user-a"))
    assert notifications_allowed(connection, "user-b", "user-a")


def test_new_active_match_restores_notifications_in_both_directions() -> None:
    connection = connection_returning(("active", None))
    assert notifications_allowed(connection, "user-a", "user-b")


def test_users_without_match_history_can_receive_notifications() -> None:
    connection = connection_returning(None)
    assert notifications_allowed(connection, "user-a", "user-b")
