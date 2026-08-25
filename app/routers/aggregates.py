import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Link, SpeedRecord
from app.params import resolve_day, resolve_period
from app.schemas import AggregateItem, SpatialFilterRequest

router = APIRouter(prefix="/aggregates", tags=["aggregates"])


def _aggregate_columns():
    """Columns shared by every query that returns an AggregateItem."""
    return (
        Link.link_id,
        Link.road_name,
        Link.length,
        func.ST_AsGeoJSON(Link.geom).label("geometry"),
        func.avg(SpeedRecord.speed).label("average_speed"),
    )


def _to_aggregate_item(row) -> AggregateItem:
    return AggregateItem(
        link_id=row.link_id,
        road_name=row.road_name,
        length=row.length,
        average_speed=round(row.average_speed, 3),
        geometry=json.loads(row.geometry),
    )


@router.get("/", response_model=list[AggregateItem])
async def get_aggregates(
    day: str = Query(..., description="Day name, e.g. 'Wednesday'"),
    period: str = Query(..., description="Period name, e.g. 'AM Peak', or numeric id 1-7"),
    db: AsyncSession = Depends(get_db),
) -> list[AggregateItem]:
    """Aggregated average speed per link for the given day and time period."""
    day_id = resolve_day(day)
    period_id = resolve_period(period)

    stmt = (
        select(*_aggregate_columns())
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(SpeedRecord.day_of_week == day_id, SpeedRecord.period == period_id)
        .group_by(Link.link_id, Link.road_name, Link.length, Link.geom)
    )
    rows = (await db.execute(stmt)).all()
    return [_to_aggregate_item(row) for row in rows]


@router.get("/{link_id}", response_model=AggregateItem)
async def get_aggregate_for_link(
    link_id: int,
    day: str = Query(..., description="Day name, e.g. 'Wednesday'"),
    period: str = Query(..., description="Period name, e.g. 'AM Peak', or numeric id 1-7"),
    db: AsyncSession = Depends(get_db),
) -> AggregateItem:
    """Speed and metadata for a single road segment, for the given day and period."""
    day_id = resolve_day(day)
    period_id = resolve_period(period)

    stmt = (
        select(*_aggregate_columns())
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(
            Link.link_id == link_id,
            SpeedRecord.day_of_week == day_id,
            SpeedRecord.period == period_id,
        )
        .group_by(Link.link_id, Link.road_name, Link.length, Link.geom)
    )
    row = (await db.execute(stmt)).first()
    if row is not None:
        return _to_aggregate_item(row)

    # Distinguish "link doesn't exist" from "link exists but has no data here".
    link_exists = await db.scalar(select(Link.link_id).where(Link.link_id == link_id))
    if link_exists is None:
        raise HTTPException(status_code=404, detail=f"Link {link_id} not found")
    raise HTTPException(
        status_code=404,
        detail=f"No speed data for link {link_id} on the given day/period",
    )


@router.post("/spatial_filter/", response_model=list[AggregateItem])
async def spatial_filter(
    body: SpatialFilterRequest,
    db: AsyncSession = Depends(get_db),
) -> list[AggregateItem]:
    """Road segments intersecting a bounding box, for the given day and period."""
    day_id = resolve_day(body.day)
    period_id = resolve_period(body.period)
    min_lon, min_lat, max_lon, max_lat = body.bbox
    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

    stmt = (
        select(*_aggregate_columns())
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(
            SpeedRecord.day_of_week == day_id,
            SpeedRecord.period == period_id,
            func.ST_Intersects(Link.geom, envelope),
        )
        .group_by(Link.link_id, Link.road_name, Link.length, Link.geom)
    )
    rows = (await db.execute(stmt)).all()
    return [_to_aggregate_item(row) for row in rows]
