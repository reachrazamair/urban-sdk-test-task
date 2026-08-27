#!/usr/bin/env bash
# One-shot dev environment setup: deps, database, schema.
# For everything including the data and the API, use bin/run.sh instead —
# this one is here for anyone who wants just the environment prepared.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Urban SDK traffic API setup"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

# Auto-fall back to a free port if the configured one is already taken.
free_port() {
  local port=$1
  while lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; do
    port=$((port + 1))
  done
  echo "$port"
}

if ! docker ps -a --format '{{.Names}}' | grep -qx urban_sdk_db; then
  pg_port=$(grep '^POSTGRES_PORT=' .env | cut -d= -f2 || true); pg_port=${pg_port:-5432}
  free=$(free_port "$pg_port")
  if [ "$free" != "$pg_port" ]; then
    echo "==> Port $pg_port is taken, using $free for Postgres instead"
    sed -i.bak "s/^POSTGRES_PORT=.*/POSTGRES_PORT=$free/; s#localhost:$pg_port/#localhost:$free/#" .env
    rm -f .env.bak
  fi
fi

echo "==> Installing Python dependencies"
uv sync

echo "==> Starting Postgres/PostGIS"
docker compose up -d db

echo "==> Waiting for database to be healthy"
until [ "$(docker inspect -f '{{.State.Health.Status}}' urban_sdk_db 2>/dev/null)" = "healthy" ]; do
  sleep 1
done

echo "==> Initializing schema"
uv run python -m scripts.init_db

echo "==> Done. Load the data and start the API with: ./bin/run.sh"
