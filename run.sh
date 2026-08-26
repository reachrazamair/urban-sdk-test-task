#!/usr/bin/env bash
# One-command full startup: database, schema, data, and the API — all of it.
# Run this and everything is up; no other command needed.
#
#   ./run.sh
#
# Re-running it is safe: it skips steps that are already done (schema
# creation and data loading are both no-ops if already in place), and just
# restarts the API. To stop everything, see stop.sh.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Urban SDK traffic API — starting the full stack"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

echo "==> Installing Python dependencies"
uv sync --group notebook >/dev/null

echo "==> Starting Postgres/PostGIS + Adminer"
docker compose up -d db adminer

echo "==> Waiting for the database to be healthy"
until [ "$(docker inspect -f '{{.State.Health.Status}}' urban_sdk_db 2>/dev/null)" = "healthy" ]; do
  sleep 1
done

echo "==> Initializing schema"
uv run python -m scripts.init_db

echo "==> Checking for existing data"
LINK_COUNT="$(uv run python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from app.database import engine

async def count():
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text('SELECT COUNT(*) FROM links'))
            return result.scalar()
        except ProgrammingError:
            return 0

print(asyncio.run(count()))
" 2>/dev/null | tail -1)"

if [ "${LINK_COUNT:-0}" -gt 0 ]; then
  echo "==> Data already loaded ($LINK_COUNT links) — skipping ingestion"
else
  echo "==> Loading link + speed data (downloads ~25MB, first run only — takes a minute or two)"
  uv run python -m app.ingestion.load_data
fi

echo "==> Starting the API"
mkdir -p .run
if [ -f .run/api.pid ] && kill -0 "$(cat .run/api.pid)" 2>/dev/null; then
  echo "    already running (pid $(cat .run/api.pid))"
else
  nohup uv run uvicorn app.main:app --reload >.run/api.log 2>&1 &
  echo $! >.run/api.pid
  sleep 2
fi

echo ""
echo "==> Everything is up:"
echo "    API           http://localhost:8000          (interactive docs at /docs)"
echo "    Adminer       http://localhost:8080           (server: db, user/pass/db: urbansdk)"
echo "    API logs      tail -f .run/api.log"
echo ""
echo "    Notebook (optional, needs MAPBOX_TOKEN in .env):"
echo "      uv run jupyter lab notebooks/visualization.ipynb"
echo ""
echo "    To stop everything:  ./stop.sh"
