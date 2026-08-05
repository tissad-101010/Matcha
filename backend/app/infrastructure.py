"""Small connectivity checks for the mandatory infrastructure services."""

from collections.abc import Mapping

import boto3
import psycopg
from botocore.exceptions import BotoCoreError, ClientError
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError


def check_dependencies(config: Mapping[str, object]) -> dict[str, bool]:
    """Check durable storage, ephemeral storage and private object storage."""
    checks = {
        "postgres": _check_postgres(str(config["DATABASE_URL"])),
        "valkey": _check_valkey(str(config["VALKEY_URL"])),
        "minio": _check_minio(config),
    }
    return checks


def _check_postgres(database_url: str) -> bool:
    try:
        with (
            psycopg.connect(database_url, connect_timeout=2) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except psycopg.Error:
        return False


def _check_valkey(valkey_url: str) -> bool:
    try:
        client = Redis.from_url(valkey_url, socket_connect_timeout=2, socket_timeout=2)
        return bool(client.ping())
    except (RedisConnectionError, RedisTimeoutError):
        return False


def _check_minio(config: Mapping[str, object]) -> bool:
    client = boto3.client(
        "s3",
        endpoint_url=str(config["S3_ENDPOINT_URL"]),
        region_name=str(config["S3_REGION"]),
        aws_access_key_id=str(config["S3_ACCESS_KEY"]),
        aws_secret_access_key=str(config["S3_SECRET_KEY"]),
    )
    try:
        for bucket in config["S3_BUCKETS"]:  # type: ignore[union-attr]
            client.head_bucket(Bucket=bucket)
    except (BotoCoreError, ClientError):
        return False
    return True
