"""HTTP contract tests for tag catalogue endpoints."""

from flask.testing import FlaskClient


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0
        session["csrf_token"] = "csrf-test"


def test_tag_search_requires_auth_and_has_metadata(client: FlaskClient, monkeypatch) -> None:
    assert client.get("/api/v1/tags").status_code == 401
    authenticate(client)
    monkeypatch.setattr(
        "app.routes.tags.search_tags",
        lambda _url, query, limit: [{"id": "1", "name": f"{query}:{limit}"}],
    )
    response = client.get("/api/v1/tags?query=cinema&limit=5")
    assert response.status_code == 200
    assert response.get_json()["meta"]["count"] == 1


def test_tag_creation_requires_csrf(client: FlaskClient) -> None:
    authenticate(client)
    assert client.post("/api/v1/tags", json={"name": "Cinéma"}).status_code == 403


def test_profile_tag_replacement_returns_fresh_profile(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    selected: list[int] = []
    monkeypatch.setattr(
        "app.routes.tags.replace_profile_tags", lambda _url, _user, ids: selected.append(len(ids))
    )
    monkeypatch.setattr(
        "app.routes.tags.private_profile", lambda *_args: {"tags": [{"name": "Cinéma"}]}
    )
    response = client.put(
        "/api/v1/me/tags",
        json={"tag_ids": ["e8d7a810-4cb8-47ec-b359-70fdc5288a9a"]},
        headers={"X-CSRF-Token": "csrf-test"},
    )
    assert response.status_code == 200
    assert selected == [1]
    assert response.get_json()["data"]["tags"][0]["name"] == "Cinéma"
