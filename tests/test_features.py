"""
test_features.py
----------------
Unit tests for feature engineering functions.
All tests use in-memory Polars DataFrames — no data files required.

Run with: pytest tests/
"""
import polars as pl
from datetime import datetime, date

from zh_tram_flow.features.delays import add_delay_features
from zh_tram_flow.features.temporal import add_time_features, add_interaction_features


# ── delays.py ────────────────────────────────────────────────────────────────

def test_delay_delta_positive_when_delay_grew():
    """delay_delta > 0 means delay grew at this stop."""
    df = pl.DataFrame({
        "departure_delay": [20],
        "arrival_delay": [10],
        "departure_schedule": [datetime(2024, 1, 1, 8, 5)],
        "arrival_schedule": [datetime(2024, 1, 1, 8, 0)],
    })
    result = add_delay_features(df)
    assert result["delay_delta"][0] == 10


def test_delay_delta_negative_when_delay_recovered():
    """delay_delta < 0 means the tram recovered time at this stop."""
    df = pl.DataFrame({
        "departure_delay": [-5],
        "arrival_delay": [10],
        "departure_schedule": [datetime(2024, 1, 1, 8, 5)],
        "arrival_schedule": [datetime(2024, 1, 1, 8, 0)],
    })
    result = add_delay_features(df)
    assert result["delay_delta"][0] == -15


def test_dwell_time_in_seconds():
    """dwell_time = scheduled departure − scheduled arrival (seconds)."""
    df = pl.DataFrame({
        "departure_delay": [0],
        "arrival_delay": [0],
        "departure_schedule": [datetime(2024, 1, 1, 8, 5)],   # 08:05
        "arrival_schedule": [datetime(2024, 1, 1, 8, 0)],     # 08:00
    })
    result = add_delay_features(df)
    assert result["dwell_time"][0] == 300  # 5 min × 60 s = 300 s


def test_dwell_time_zero_for_no_planned_stop():
    """dwell_time = 0 when departure_schedule == arrival_schedule."""
    df = pl.DataFrame({
        "departure_delay": [0],
        "arrival_delay": [0],
        "departure_schedule": [datetime(2024, 1, 1, 8, 0)],
        "arrival_schedule": [datetime(2024, 1, 1, 8, 0)],
    })
    result = add_delay_features(df)
    assert result["dwell_time"][0] == 0


# ── temporal.py ──────────────────────────────────────────────────────────────

def test_hour_extracted_from_arrival_schedule():
    """Peak hour is 21h — confirm extraction is correct."""
    df = pl.DataFrame({
        "arrival_schedule": [datetime(2024, 3, 14, 21, 0, 0)],
        "operating_date": [date(2024, 3, 14)],
    })
    result = add_time_features(df)
    assert result["hour"][0] == 21


def test_season_mapping():
    """1=winter 2=spring 3=summer 4=fall — December wraps to winter."""
    df = pl.DataFrame({
        "arrival_schedule": [
            datetime(2024, 1, 15, 8, 0),   # winter
            datetime(2024, 4, 15, 8, 0),   # spring
            datetime(2024, 7, 15, 8, 0),   # summer
            datetime(2024, 10, 15, 8, 0),  # fall
            datetime(2024, 12, 15, 8, 0),  # winter (December)
        ],
        "operating_date": [
            date(2024, 1, 15), date(2024, 4, 15), date(2024, 7, 15),
            date(2024, 10, 15), date(2024, 12, 15),
        ],
    })
    result = add_time_features(df)
    assert result["season"].to_list() == [1, 2, 3, 4, 1]


def test_is_weekend_flag():
    """Saturday and Sunday are True; Monday is False."""
    df = pl.DataFrame({
        # 2024-01-06 = Saturday, 2024-01-07 = Sunday, 2024-01-08 = Monday
        "arrival_schedule": [
            datetime(2024, 1, 6, 10, 0),
            datetime(2024, 1, 7, 10, 0),
            datetime(2024, 1, 8, 10, 0),
        ],
        "operating_date": [date(2024, 1, 6), date(2024, 1, 7), date(2024, 1, 8)],
    })
    result = add_time_features(df)
    assert result["is_weekend"].to_list() == [True, True, False]


def test_is_november_flag():
    """November flag is True only in month 11."""
    df = pl.DataFrame({
        "arrival_schedule": [
            datetime(2024, 11, 1, 8, 0),
            datetime(2024, 10, 31, 8, 0),
        ],
        "operating_date": [date(2024, 11, 1), date(2024, 10, 31)],
    })
    result = add_time_features(df)
    assert result["is_november"].to_list() == [True, False]


def test_gtfs_year_epoch():
    """Before 2024-01-01 → j23; from 2024-01-01 → j24_j25."""
    df = pl.DataFrame({
        "arrival_schedule": [datetime(2023, 12, 31, 23, 59), datetime(2024, 1, 1, 0, 0)],
        "operating_date": [date(2023, 12, 31), date(2024, 1, 1)],
    })
    result = add_time_features(df)
    assert result["gtfs_year"].to_list() == ["j23", "j24_j25"]
