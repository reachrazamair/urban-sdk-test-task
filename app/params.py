"""Query-param resolution shared across endpoints.

Accepts either human-friendly names (as shown in the assignment's example
requests, e.g. day="Wednesday", period="AM Peak") or their numeric ids, and
raises a 400 with a helpful message on anything else.
"""

from fastapi import HTTPException

from app.constants import DAY_NAME_TO_INT, PERIOD_NAME_TO_ID, TIME_PERIODS


def resolve_day(day: str) -> int:
    key = day.strip().lower()
    if key in DAY_NAME_TO_INT:
        return DAY_NAME_TO_INT[key]
    raise HTTPException(
        status_code=400,
        detail=f"Invalid day '{day}'. Expected one of {list(DAY_NAME_TO_INT)}.",
    )


def resolve_period(period: str) -> int:
    key = period.strip().lower()
    if key.isdigit() and int(key) in TIME_PERIODS:
        return int(key)
    if key in PERIOD_NAME_TO_ID:
        return PERIOD_NAME_TO_ID[key]
    valid_names = [name for name, _, _ in TIME_PERIODS.values()]
    raise HTTPException(
        status_code=400,
        detail=f"Invalid period '{period}'. Expected one of {valid_names} or ids 1-7.",
    )
