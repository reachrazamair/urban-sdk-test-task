import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Link, SpeedRecord
from app.params import resolve_day, resolve_period
from app.schemas import AggregateItem

router = APIRouter(prefix="/aggregates", tags=["aggregates"])


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
        select(
            Link.link_id,
            Link.road_name,
            Link.length,
            func.ST_AsGeoJSON(Link.geom).label("geometry"),
            func.avg(SpeedRecord.speed).label("average_speed"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(SpeedRecord.day_of_week == day_id, SpeedRecord.period == period_id)
        .group_by(Link.link_id, Link.road_name, Link.length, Link.geom)
    )
    rows = (await db.execute(stmt)).all()

    return [
        AggregateItem(
            link_id=row.link_id,
            road_name=row.road_name,
            length=row.length,
            average_speed=round(row.average_speed, 3),
            geometry=json.loads(row.geometry),
        )
        for row in rows
    ]
