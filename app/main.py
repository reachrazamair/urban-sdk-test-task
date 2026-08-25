from fastapi import FastAPI

from app.routers import aggregates

app = FastAPI(
    title="Urban SDK Traffic Analytics API",
    description="Geospatial traffic aggregation microservice for Duval County speed data.",
    version="0.1.0",
)

app.include_router(aggregates.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
