#!/usr/bin/env bash
# Shuts down everything run.sh started: the API process and the Postgres/Adminer
# containers. The database volume (loaded data) is left in place — next
# ./run.sh comes back up instantly without reloading.
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .run/api.pid ] && kill -0 "$(cat .run/api.pid)" 2>/dev/null; then
  echo "==> Stopping the API (pid $(cat .run/api.pid))"
  kill "$(cat .run/api.pid)"
  rm -f .run/api.pid
else
  echo "==> API not running"
fi

echo "==> Stopping Postgres/PostGIS + Adminer"
docker compose down

echo "==> Done. (Data volume kept — run ./run.sh to come back up instantly.)"
