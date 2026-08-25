"""Download the two source Parquet datasets and load them into Postgres/PostGIS.

Idempotent: truncates both tables before loading, so it's safe to re-run.
"""

import asyncio
import json
from pathlib import Path

import httpx
import pandas as pd
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import text

from app.database import engine
from app.models import Link, SpeedRecord

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
LINK_INFO_URL = "https://cdn.urbansdk.com/data-engineering-interview/link_info.parquet.gz"
SPEED_URL = "https://cdn.urbansdk.com/data-engineering-interview/duval_jan1_2024.parquet.gz"

BATCH_SIZE = 5000


def _download(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {dest}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return dest


def _load_links(path: Path) -> list[dict]:
    df = pd.read_parquet(path).rename(columns={"_length": "length"})
    rows = []
    for row in df.itertuples(index=False):
        geom = shape(json.loads(row.geo_json))
        rows.append(
            {
                "link_id": int(row.link_id),
                "road_name": None if pd.isna(row.road_name) else row.road_name,
                "length": float(row.length),
                "funclass_id": int(row.funclass_id),
                "speed_category": int(row.usdk_speed_category),
                "volume_value": int(row.volume_value),
                "geom": from_shape(geom, srid=4326),
            }
        )
    return rows


def _load_speed_records(path: Path) -> list[dict]:
    df = pd.read_parquet(path)
    df["date_time"] = pd.to_datetime(df["date_time"])
    return [
        {
            "link_id": int(row.link_id),
            "timestamp": row.date_time,
            "speed": float(row.average_speed),
            "day_of_week": int(row.day_of_week),
            "period": int(row.period),
        }
        for row in df.itertuples(index=False)
    ]


async def _bulk_insert(conn, table, rows: list[dict]) -> None:
    for i in range(0, len(rows), BATCH_SIZE):
        await conn.execute(table.insert(), rows[i : i + BATCH_SIZE])


async def main() -> None:
    link_info_path = _download(LINK_INFO_URL, DATA_DIR / "link_info.parquet.gz")
    speed_path = _download(SPEED_URL, DATA_DIR / "duval_jan1_2024.parquet.gz")

    print("Parsing link_info...")
    link_rows = _load_links(link_info_path)
    print(f"Parsing speed data... ({len(link_rows)} links)")
    speed_rows = _load_speed_records(speed_path)
    print(f"{len(speed_rows)} speed records")

    async with engine.begin() as conn:
        print("Truncating existing data...")
        await conn.execute(text("TRUNCATE TABLE speed_records, links RESTART IDENTITY CASCADE"))

        print("Inserting links...")
        await _bulk_insert(conn, Link.__table__, link_rows)

        print("Inserting speed records...")
        await _bulk_insert(conn, SpeedRecord.__table__, speed_rows)

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
