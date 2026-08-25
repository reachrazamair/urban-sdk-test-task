"""Time-of-day periods and day-of-week encoding used by the source dataset.

The speed dataset ships with precomputed `day_of_week` and `period` columns
rather than raw timestamps alone, so we mirror that encoding here instead of
re-deriving it per query.

`day_of_week` runs Sunday=1 .. Saturday=7. This was verified against the
sample dataset directly: its only date, 2024-01-01, is a Monday, and every
row for that date is encoded as day_of_week=2.
"""

DAY_NAME_TO_INT = {
    "sunday": 1,
    "monday": 2,
    "tuesday": 3,
    "wednesday": 4,
    "thursday": 5,
    "friday": 6,
    "saturday": 7,
}

# period id -> (name, start_hour, end_hour); end_hour is inclusive.
TIME_PERIODS = {
    1: ("Overnight", 0, 3),
    2: ("Early Morning", 4, 6),
    3: ("AM Peak", 7, 9),
    4: ("Midday", 10, 12),
    5: ("Early Afternoon", 13, 15),
    6: ("PM Peak", 16, 18),
    7: ("Evening", 19, 23),
}

PERIOD_NAME_TO_ID = {name.lower(): pid for pid, (name, _, _) in TIME_PERIODS.items()}
