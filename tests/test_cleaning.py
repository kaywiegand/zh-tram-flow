"""
test_cleaning.py
----------------
Unit tests for structural cleaning pipeline functions.
All tests use in-memory Polars DataFrames — no data files required.

Run with: pytest tests/
"""
import polars as pl
from datetime import datetime

import pytest
from zh_tram_flow.data.cleaning import (
    filter_extreme_delays,
    filter_delay_mismatch,
    remove_duplicates,
    clip_physical_bounds,
    DELAY_MAX_ABS,
)


def test_filter_extreme_delays_removes_above_threshold():
    """Rows where |arrival_delay| or |departure_delay| > max_abs are dropped."""
    lf = pl.DataFrame({
        "arrival_delay": [10, DELAY_MAX_ABS + 1, -10, DELAY_MAX_ABS],
        "departure_delay": [10, 10, 10, 10],
    }).lazy()
    result = filter_extreme_delays(lf, max_abs=DELAY_MAX_ABS).collect()
    assert len(result) == 3
    assert (DELAY_MAX_ABS + 1) not in result["arrival_delay"].to_list()


def test_filter_extreme_delays_checks_departure_too():
    """departure_delay beyond threshold also triggers removal."""
    lf = pl.DataFrame({
        "arrival_delay": [10, 10],
        "departure_delay": [10, DELAY_MAX_ABS + 1],
    }).lazy()
    result = filter_extreme_delays(lf, max_abs=DELAY_MAX_ABS).collect()
    assert len(result) == 1


def test_filter_extreme_delays_keeps_boundary():
    """Row at exactly max_abs is kept (filter is <=)."""
    lf = pl.DataFrame({
        "arrival_delay": [DELAY_MAX_ABS],
        "departure_delay": [DELAY_MAX_ABS],
    }).lazy()
    result = filter_extreme_delays(lf).collect()
    assert len(result) == 1


def test_remove_duplicates():
    """Fully identical rows are collapsed to one."""
    lf = pl.DataFrame({
        "trip_id": [1, 1, 2],
        "arrival_delay": [30, 30, 45],
    }).lazy()
    result = remove_duplicates(lf).collect()
    assert len(result) == 2


def test_filter_delay_mismatch_drops_null_schedule():
    """Rows with null arrival_schedule or null arrival_delay are removed."""
    lf = pl.DataFrame({
        "arrival_schedule": [datetime(2024, 3, 1, 8, 0), None],
        "arrival_delay": [15, 15],
    }).lazy()
    result = filter_delay_mismatch(lf).collect()
    assert len(result) == 1


def test_filter_delay_mismatch_drops_null_delay():
    lf = pl.DataFrame({
        "arrival_schedule": [datetime(2024, 3, 1, 8, 0), datetime(2024, 3, 1, 9, 0)],
        "arrival_delay": [15, None],
    }).lazy()
    result = filter_delay_mismatch(lf).collect()
    assert len(result) == 1


def test_clip_physical_bounds_humidity():
    """Humidity is clipped to [0, 100]."""
    lf = pl.DataFrame({"humidity": [-5.0, 50.0, 120.0]}).lazy()
    result = clip_physical_bounds(lf).collect()
    assert result["humidity"].to_list() == [0.0, 50.0, 100.0]
