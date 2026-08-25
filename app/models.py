from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Link(Base):
    """A road segment, with its geometry and static metadata."""

    __tablename__ = "links"

    link_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    road_name: Mapped[str | None] = mapped_column(String, nullable=True)
    length: Mapped[float] = mapped_column(Float, nullable=False)
    funclass_id: Mapped[int] = mapped_column(Integer, nullable=False)
    speed_category: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_value: Mapped[int] = mapped_column(Integer, nullable=False)
    # Source geometries are all MultiLineString, not plain LineString.
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=False
    )

    speed_records: Mapped[list["SpeedRecord"]] = relationship(back_populates="link")


class SpeedRecord(Base):
    """An hourly average-speed observation for a single link."""

    __tablename__ = "speed_records"
    __table_args__ = (
        Index("ix_speed_records_link_day_period", "link_id", "day_of_week", "period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.link_id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)

    link: Mapped["Link"] = relationship(back_populates="speed_records")
