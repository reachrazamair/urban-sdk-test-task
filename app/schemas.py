from pydantic import BaseModel, Field


class AggregateItem(BaseModel):
    link_id: int
    road_name: str | None
    length: float
    average_speed: float
    geometry: dict


class SlowLinkItem(BaseModel):
    link_id: int
    road_name: str | None
    length: float
    geometry: dict
    average_speed: float
    slow_day_count: int


class SpatialFilterRequest(BaseModel):
    day: str
    period: str
    bbox: list[float] = Field(
        min_length=4,
        max_length=4,
        description="[min_lon, min_lat, max_lon, max_lat]",
    )
