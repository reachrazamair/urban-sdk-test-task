from pydantic import BaseModel


class AggregateItem(BaseModel):
    link_id: int
    road_name: str | None
    length: float
    average_speed: float
    geometry: dict
