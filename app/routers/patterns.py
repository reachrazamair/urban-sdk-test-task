import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Link, SpeedRecord
from app.params import resolve_period
from app.schemas import SlowLinkItem

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("/slow_links/", response_model=list[SlowLinkItem])
async def get_slow_links(
    period: str = Query(..., description="Period name, e.g. 'AM Peak', or numeric id 1-7"),
    threshold: float = Query(..., description="Average speed threshold, in mph"),
    min_days: int = Query(
        ..., ge=1, description="Minimum number of days in the week below the threshold"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[SlowLinkItem]:
    """Links averaging below `threshold` mph for at least `min_days` days in the period.

    "Day" here means a distinct calendar date, computed from each speed
    record's timestamp — not day_of_week — so this holds up against a full
    multi-week dataset. Note: the sample dataset only covers a single date
    (2024-01-01), so only min_days=1 can ever match against it; the query
    itself is written to be correct for any date range.
    """
    period_id = resolve_period(period)

    day_bucket = func.date_trunc("day", SpeedRecord.timestamp)
    daily_avg = (
        select(
            SpeedRecord.link_id.label("link_id"),
            func.avg(SpeedRecord.speed).label("day_avg_speed"),
        )
        .where(SpeedRecord.period == period_id)
        .group_by(SpeedRecord.link_id, day_bucket)
        .subquery()
    )

    slow = (
        select(
            daily_avg.c.link_id.label("link_id"),
            func.count().label("slow_day_count"),
            func.avg(daily_avg.c.day_avg_speed).label("average_speed"),
        )
        .where(daily_avg.c.day_avg_speed < threshold)
        .group_by(daily_avg.c.link_id)
        .having(func.count() >= min_days)
        .subquery()
    )

    stmt = select(
        Link.link_id,
        Link.road_name,
        Link.length,
        func.ST_AsGeoJSON(Link.geom).label("geometry"),
        slow.c.average_speed,
        slow.c.slow_day_count,
    ).join(slow, slow.c.link_id == Link.link_id)

    rows = (await db.execute(stmt)).all()
    return [
        SlowLinkItem(
            link_id=row.link_id,
            road_name=row.road_name,
            length=row.length,
            geometry=json.loads(row.geometry),
            average_speed=round(row.average_speed, 3),
            slow_day_count=row.slow_day_count,
        )
        for row in rows
    ]
