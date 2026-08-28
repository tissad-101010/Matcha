"""Business-level refusals for profile interactions."""

import pytest

from app.interactions.service import (
    InteractionError,
    like_profile,
    record_profile_visit,
    unlike_profile,
)


def test_like_requires_a_main_photo(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.interactions.service.upsert_like_and_match", lambda *_args: "photo_required"
    )
    with pytest.raises(InteractionError) as raised:
        like_profile("database", "source", "target")
    assert raised.value.code == "main_photo_required"
    assert raised.value.status == 403


def test_unlike_requires_an_active_like(monkeypatch) -> None:
    monkeypatch.setattr("app.interactions.service.deactivate_pair", lambda *_args: None)
    with pytest.raises(InteractionError) as raised:
        unlike_profile("database", "source", "target")
    assert raised.value.code == "not_found"


def test_visit_refuses_self_and_inaccessible_profiles(monkeypatch) -> None:
    with pytest.raises(InteractionError) as self_visit:
        record_profile_visit("database", "same", "same")
    monkeypatch.setattr("app.interactions.service.insert_visit", lambda *_args: (False, None))
    with pytest.raises(InteractionError) as unavailable:
        record_profile_visit("database", "visitor", "blocked")
    assert self_visit.value.code == "self_interaction"
    assert unavailable.value.code == "not_found"
