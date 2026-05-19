"""Final feature pipeline: filters, feature construction, column selection."""
import polars as pl
from datetime import date

from .delays import add_delay_features
from .events import add_event_features
from .network import compute_network_stats, apply_network_features
from .temporal import add_time_features, add_interaction_features
from .weather import add_weather_flags

# Raw columns kept as model inputs (identifiers + targets + continuous signals)
KEEP_RAW = [
    "operating_date", "trip_id", "line_name", "stop_name",
    "stop_lat", "stop_lon", "district_nr",
    "arrival_delay", "departure_delay",
    "temperature", "precipitation", "wind_speed", "flood_intensity",
    "event_name", "event_type", "event_size",
]

# Engineered features added by this pipeline
ENGINEERED = [
    "hour", "weekday", "month", "year", "season",
    "is_weekend", "is_november", "gtfs_year",
    "has_rain", "has_heavy_rain", "has_snow", "has_flood", "is_hot",
    "is_holiday", "has_event", "event_weight",
    "delay_delta", "dwell_time",
    "n_lines_at_stop", "n_stops_line", "is_start_stop", "is_end_stop",
    "event_weight_x_hour", "is_late_night_weekend",
]


def apply_lf_clean(lf: pl.LazyFrame, is_test: bool = False) -> pl.LazyFrame:
    """Apply lf_clean filters. is_test=True also removes Nov/Dec 2025 GTFS artefact."""
    lf = (
        lf
        .filter(pl.col("canceled") == False)
        .filter(pl.col("stop_sequence") > 1)
        .filter(pl.col("line_name") != "E")
    )
    if is_test:
        lf = lf.filter(
            ~((pl.col("operating_date").dt.year() == 2025) &
              (pl.col("operating_date").dt.month() >= 11))
        )
    return lf


def build_features(lf: pl.LazyFrame, network_stats: dict | None = None) -> pl.LazyFrame:
    """Apply all feature functions in sequence."""
    lf = add_time_features(lf)
    lf = add_weather_flags(lf)
    lf = add_event_features(lf)
    lf = add_delay_features(lf)
    lf = add_interaction_features(lf)
    if network_stats is not None:
        lf = apply_network_features(lf, network_stats["stop_stats"], network_stats["line_stats"])
    return lf


def select_final_columns(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Keep only model-relevant columns — drop raw signals replaced by flags."""
    cols = [c for c in KEEP_RAW + ENGINEERED if c in lf.collect_schema().names()]
    return lf.select(cols)
