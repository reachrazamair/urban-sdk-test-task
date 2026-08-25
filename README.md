# Urban SDK — Geospatial Traffic Analytics Microservice

A FastAPI microservice that ingests link-level traffic speed data for Duval
County, FL into PostgreSQL/PostGIS and exposes REST endpoints for spatial and
temporal aggregation of road segment speeds — with a companion Jupyter
notebook for Mapbox visualization.

## What's here

- **API** — FastAPI + SQLAlchemy service for querying average speeds per
  road link, filtered by day of week, time-of-day period, and/or a spatial
  bounding box.
- **Data model** — PostGIS-backed `Link` (road segment geometry) and
  `SpeedRecord` (hourly speed observations) tables.
- **Notebook** — pulls aggregated data from the API and renders it on a
  Mapbox choropleth, colored by average speed.
- **Architecture** — diagram of the ingestion → storage → API → visualization
  flow.

## Status

Work in progress — implementation details, setup instructions, and the
architecture diagram will land here as the service is built out.
