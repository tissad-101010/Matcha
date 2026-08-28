"""HTTP authorization contract for local conversation hiding."""

from flask.testing import FlaskClient

CONVERSATION_ID = "00000000-0000-4000-8000-000000000050"


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_hide_requires_authentication_and_csrf(client: FlaskClient) -> None:
    path = f"/api/v1/conversations/{CONVERSATION_ID}/hide"
    assert client.post(path).status_code == 401
    authenticate(client)
    assert client.post(path).status_code == 403


def test_member_can_hide_conversation_locally(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    calls = []
    monkeypatch.setattr(
        "app.routes.conversations.hide_conversation", lambda *args: calls.append(args)
    )
    response = client.post(
        f"/api/v1/conversations/{CONVERSATION_ID}/hide",
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 204
    assert str(calls[0][-1]) == CONVERSATION_ID


def test_unknown_or_unauthorized_conversation_is_not_disclosed(
    client: FlaskClient, monkeypatch
) -> None:
    from app.interactions.service import InteractionError

    authenticate(client)

    def refuse(*_args):  # type: ignore[no-untyped-def]
        raise InteractionError("not_found", "Conversation introuvable.", 404)

    monkeypatch.setattr("app.routes.conversations.hide_conversation", refuse)
    response = client.post(
        f"/api/v1/conversations/{CONVERSATION_ID}/hide",
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
