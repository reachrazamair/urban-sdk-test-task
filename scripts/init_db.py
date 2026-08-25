"""Create the PostGIS extension (if missing) and all ORM tables."""

import asyncio

from sqlalchemy import text

from app import models  # noqa: F401 -- registers models on Base.metadata
from app.database import Base, engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized.")


if __name__ == "__main__":
    asyncio.run(init_db())
