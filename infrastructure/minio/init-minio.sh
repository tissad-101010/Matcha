#!/bin/sh
set -eu

until mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    sleep 2
done

echo "MinIO est prêt, initialisation des buckets privés."

for bucket in profile-photos gallery temporary; do
    mc mb --ignore-existing "local/$bucket"
    mc anonymous set none "local/$bucket"
done
