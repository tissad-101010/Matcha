"""HTTP contract tests for advanced profile search."""

from uuid import UUID

from flask.testing import FlaskClient


def authenticate(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session["user_id"] = "e8d7a810-4cb8-47ec-b359-70fdc5288a9a"
        session["auth_version"] = 0


def test_search_requires_authentication(client: FlaskClient) -> None:
    assert client.get("/api/v1/search/profiles").status_code == 401


def test_search_rejects_unknown_location(client: FlaskClient) -> None:
    authenticate(client)
    response = client.get("/api/v1/search/profiles?location_id=not-a-uuid")
    assert response.status_code == 422
    assert "location_id" in response.get_json()["error"]["fields"]


def test_search_combines_validated_criteria(client: FlaskClient, monkeypatch) -> None:
    authenticate(client)
    captured = []

    def fake_suggestions(_database_url, _user_id, query):  # type: ignore[no-untyped-def]
        captured.append(query)
        return {"data": [], "meta": {"next_cursor": None, "count": 0}}

    monkeypatch.setattr("app.routes.search.suggestions", fake_suggestions)
    location_id = "00000000-0000-4000-8000-000000000010"
    tag_id = "00000000-0000-4000-8000-000000000020"
    response = client.get(
        f"/api/v1/search/profiles?age_min=25&age_max=40&popularity_min=20"
        f"&location_id={location_id}&tag_ids={tag_id}&sort=tags"
    )
    assert response.status_code == 200
    assert str(captured[0].location_id) == location_id
    assert captured[0].tag_ids == {UUID(tag_id)}
    assert captured[0].sort == "tags"
