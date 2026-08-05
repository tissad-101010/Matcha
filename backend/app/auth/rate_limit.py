"""Atomic Valkey rate limiting for authentication attempts."""

from redis import Redis

LOGIN_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60
INCREMENT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return current
"""


def _login_key(subject: str) -> str:
    return f"matcha:rate:login:{subject}"


def login_allowed(valkey_url: str, subject: str) -> bool:
    """Allow five attempts per username/IP pair in a fixed 15-minute window."""
    client = Redis.from_url(valkey_url, socket_timeout=2)
    count = client.eval(INCREMENT_SCRIPT, 1, _login_key(subject), LOGIN_WINDOW_SECONDS)
    return bool(count <= LOGIN_LIMIT)


def clear_login_limit(valkey_url: str, subject: str) -> None:
    """Reset the failed-attempt counter after successful authentication."""
    Redis.from_url(valkey_url, socket_timeout=2).delete(_login_key(subject))
