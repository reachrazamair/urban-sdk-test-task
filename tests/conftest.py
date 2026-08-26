"""Shared fixtures. Tests hit the app in-process (ASGI transport, no socket)
against the real Postgres/PostGIS instance — start it first with
`./bin/run.sh` (or at least `docker compose up -d db` + a loaded dataset).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
