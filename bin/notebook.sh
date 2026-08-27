#!/usr/bin/env bash
# Launches the Mapbox visualization notebook. Needs the API running and MAPBOX_TOKEN set in .env.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ] || ! grep -Eq '^MAPBOX_TOKEN=.+' .env; then
  echo "Set MAPBOX_TOKEN in .env first — get a free token at https://mapbox.com"
  exit 1
fi

if ! curl -s -o /dev/null "http://localhost:8000/health"; then
  echo "The API isn't running — start it first with ./bin/run.sh"
  exit 1
fi

echo "==> Installing notebook dependencies"
uv sync --group notebook >/dev/null

echo "==> Launching Jupyter Lab — open notebooks/visualization.ipynb and run all cells"
uv run jupyter lab --KernelManager.transport=ipc notebooks/visualization.ipynb
