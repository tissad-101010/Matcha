#!/bin/sh
set -eu

until mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    sleep 2
done

echo "MinIO est prêt, initialisation des buckets privés."

retry() {
    until "$@" >/dev/null 2>&1; do
        sleep 2
    done
}

for bucket in profile-photos gallery temporary; do
    retry mc mb --ignore-existing "local/$bucket"
    retry mc anonymous set none "local/$bucket"
    echo "Bucket privé prêt : $bucket"
done
