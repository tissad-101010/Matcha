"""Unit tests for infrastructure checks without external network access."""

from unittest.mock import MagicMock, patch

import psycopg
from botocore.exceptions import ClientError, EndpointConnectionError
from redis.exceptions import ConnectionError as RedisConnectionError

from app.infrastructure import (
    _check_minio,
    _check_postgres,
    _check_valkey,
    check_dependencies,
)

CONFIG = {
    "DATABASE_URL": "postgresql://example",
    "VALKEY_URL": "redis://example",
    "S3_ENDPOINT_URL": "http://minio:9000",
    "S3_REGION": "us-east-1",
    "S3_ACCESS_KEY": "test-key",
    "S3_SECRET_KEY": "test-secret",
    "S3_BUCKETS": ("profile-photos", "gallery", "temporary"),
}


@patch("app.infrastructure._check_minio", return_value=True)
@patch("app.infrastructure._check_valkey", return_value=True)
@patch("app.infrastructure._check_postgres", return_value=True)
def test_check_dependencies_names_every_service(
    _postgres: MagicMock,
    _valkey: MagicMock,
    _minio: MagicMock,
) -> None:
    assert check_dependencies(CONFIG) == {"postgres": True, "valkey": True, "minio": True}


@patch("app.infrastructure.psycopg.connect")
def test_postgres_check_executes_constant_query(connect: MagicMock) -> None:
    cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (1,)

    assert _check_postgres("postgresql://example") is True
    cursor.execute.assert_called_once_with("SELECT 1")


@patch("app.infrastructure.psycopg.connect", side_effect=psycopg.OperationalError)
def test_postgres_check_handles_connection_failure(_connect: MagicMock) -> None:
    assert _check_postgres("postgresql://example") is False


@patch("app.infrastructure.Redis.from_url")
def test_valkey_check_requires_ping(from_url: MagicMock) -> None:
    from_url.return_value.ping.return_value = True

    assert _check_valkey("redis://example") is True


@patch("app.infrastructure.Redis.from_url")
def test_valkey_check_handles_connection_failure(from_url: MagicMock) -> None:
    from_url.return_value.ping.side_effect = RedisConnectionError

    assert _check_valkey("redis://example") is False


@patch("app.infrastructure.boto3.client")
def test_minio_check_requires_all_private_buckets(client_factory: MagicMock) -> None:
    assert _check_minio(CONFIG) is True
    assert client_factory.return_value.head_bucket.call_count == 3


@patch("app.infrastructure.boto3.client")
def test_minio_check_handles_missing_bucket(client_factory: MagicMock) -> None:
    client_factory.return_value.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadBucket",
    )

    assert _check_minio(CONFIG) is False


@patch("app.infrastructure.boto3.client")
def test_minio_check_handles_connection_failure(client_factory: MagicMock) -> None:
    client_factory.return_value.head_bucket.side_effect = EndpointConnectionError(
        endpoint_url="http://minio:9000"
    )

    assert _check_minio(CONFIG) is False
