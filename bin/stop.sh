#!/usr/bin/env bash
# Stops the API and containers; keeps the data volume so run.sh comes back up fast.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .run/api.pid ] && kill -0 "$(cat .run/api.pid)" 2>/dev/null; then
  echo "==> Stopping the API (pid $(cat .run/api.pid))"
  kill "$(cat .run/api.pid)"
  rm -f .run/api.pid
else
  echo "==> API not running"
fi

echo "==> Stopping Postgres/PostGIS + Adminer"
docker compose down

echo "==> Done. (Data volume kept — run ./bin/run.sh to come back up instantly.)"
