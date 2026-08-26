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
