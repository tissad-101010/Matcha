"""Tests for the shared atomic login limiter."""

from app.auth.rate_limit import LOGIN_LIMIT, clear_login_limit, login_allowed


class FakeRedis:
    def __init__(self) -> None:
        self.count = 0
        self.deleted: list[str] = []

    def eval(self, _script, _keys, _key, _window):
        self.count += 1
        return self.count

    def delete(self, key: str) -> None:
        self.deleted.append(key)


def test_login_limiter_blocks_after_five_attempts(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr("app.auth.rate_limit.Redis.from_url", lambda *_args, **_kwargs: fake)

    assert all(login_allowed("redis://unused", "ip:user") for _ in range(LOGIN_LIMIT))
    assert not login_allowed("redis://unused", "ip:user")

    clear_login_limit("redis://unused", "ip:user")
    assert fake.deleted == ["matcha:rate:login:ip:user"]
