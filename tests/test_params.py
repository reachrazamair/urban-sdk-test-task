"""Unit tests for day/period parsing — pure functions, no DB needed."""

import pytest
from fastapi import HTTPException

from app.params import resolve_day, resolve_period


@pytest.mark.parametrize(
    "day,expected",
    [
        ("Monday", 2),
        ("monday", 2),
        ("  Wednesday  ", 4),
        ("Sunday", 1),
        ("Saturday", 7),
    ],
)
def test_resolve_day_valid(day, expected):
    assert resolve_day(day) == expected


def test_resolve_day_invalid():
    with pytest.raises(HTTPException) as exc:
        resolve_day("Someday")
    assert exc.value.status_code == 400


@pytest.mark.parametrize(
    "period,expected",
    [
        ("AM Peak", 3),
        ("am peak", 3),
        ("3", 3),
        ("Overnight", 1),
        ("Evening", 7),
    ],
)
def test_resolve_period_valid(period, expected):
    assert resolve_period(period) == expected


@pytest.mark.parametrize("period", ["Rush Hour", "0", "8", ""])
def test_resolve_period_invalid(period):
    with pytest.raises(HTTPException) as exc:
        resolve_period(period)
    assert exc.value.status_code == 400
