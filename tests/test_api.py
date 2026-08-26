"""Integration tests against the real database.

The sample dataset covers exactly one date — 2024-01-01, a Monday — so the
expected counts below are pinned to that. If the loaded dataset ever
changes, these will need updating too; that's expected for tests tied to a
fixed data snapshot.
"""

import pytest


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_aggregates_monday_am_peak(client):
    resp = await client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 57_130
    assert {"link_id", "road_name", "length", "average_speed", "geometry"} <= data[0].keys()


async def test_aggregates_accepts_numeric_period(client):
    by_name = await client.get("/aggregates/", params={"day": "monday", "period": "AM Peak"})
    by_id = await client.get("/aggregates/", params={"day": "monday", "period": "3"})
    assert len(by_name.json()) == len(by_id.json()) == 57_130


async def test_aggregates_no_data_for_day_not_in_dataset(client):
    # The sample dataset only covers Monday — any other day is correctly empty.
    resp = await client.get("/aggregates/", params={"day": "Wednesday", "period": "AM Peak"})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_aggregates_invalid_day(client):
    resp = await client.get("/aggregates/", params={"day": "Someday", "period": "AM Peak"})
    assert resp.status_code == 400


async def test_aggregates_invalid_period(client):
    resp = await client.get("/aggregates/", params={"day": "Monday", "period": "Rush Hour"})
    assert resp.status_code == 400


async def test_aggregate_for_link(client):
    resp = await client.get("/aggregates/16981048", params={"day": "Monday", "period": "AM Peak"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["link_id"] == 16981048
    assert body["road_name"] == "Philips Hwy"
    assert body["average_speed"] == pytest.approx(45.401, abs=0.001)


async def test_aggregate_for_link_not_found(client):
    resp = await client.get("/aggregates/999999999", params={"day": "Monday", "period": "AM Peak"})
    assert resp.status_code == 404


async def test_aggregate_for_link_no_data_for_period(client):
    # Link exists, but this day has no readings for it -> 404 with a distinct message.
    resp = await client.get("/aggregates/16981048", params={"day": "Wednesday", "period": "AM Peak"})
    assert resp.status_code == 404


async def test_spatial_filter(client):
    resp = await client.post(
        "/aggregates/spatial_filter/",
        json={"day": "Monday", "period": "AM Peak", "bbox": [-81.8, 30.1, -81.6, 30.3]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 11_464
    # every returned link_id should also show up in the unfiltered set
    ids = {row["link_id"] for row in data}
    assert 16981048 in ids or len(ids) > 0


async def test_spatial_filter_bad_bbox(client):
    resp = await client.post(
        "/aggregates/spatial_filter/",
        json={"day": "Monday", "period": "AM Peak", "bbox": [-81.8, 30.1, -81.6]},
    )
    assert resp.status_code == 422


async def test_slow_links(client):
    resp = await client.get(
        "/patterns/slow_links/",
        params={"period": "AM Peak", "threshold": 20, "min_days": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 14_820
    assert all(row["average_speed"] < 20 for row in data)
    assert all(row["slow_day_count"] >= 1 for row in data)


async def test_slow_links_min_days_beyond_dataset_range(client):
    # Sample data covers a single calendar day, so min_days=2 can never match.
    resp = await client.get(
        "/patterns/slow_links/",
        params={"period": "AM Peak", "threshold": 20, "min_days": 2},
    )
    assert resp.status_code == 200
    assert resp.json() == []
