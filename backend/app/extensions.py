"""Shared Flask extensions initialized by the application factory."""

from cachelib.file import FileSystemCache
from flask import Flask
from flask_session import Session
from flask_socketio import SocketIO
from redis import Redis

session = Session()
socketio = SocketIO(cors_allowed_origins=[], manage_session=False)


def init_extensions(app: Flask) -> None:
    """Attach session and real-time services without opening network connections."""
    if app.config["TESTING"]:
        # Unit tests do not require an external Valkey instance.
        app.config.update(
            SESSION_TYPE="cachelib",
            SESSION_CACHELIB=FileSystemCache(cache_dir="/tmp/matcha-test-sessions"),
            SOCKET_MESSAGE_QUEUE=None,
        )
    else:
        app.config["SESSION_REDIS"] = Redis.from_url(app.config["SESSION_REDIS_URL"])

    session.init_app(app)
    socketio.init_app(app, message_queue=app.config["SOCKET_MESSAGE_QUEUE"])
