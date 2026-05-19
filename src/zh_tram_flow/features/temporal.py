"""Temporal features: hour, weekday, month, year, season, flags, network epoch."""
import polars as pl
from datetime import date


def add_time_features(frame):
    """Add time-based features from arrival_schedule and operating_date."""
    return frame.with_columns([
        pl.col("arrival_schedule").dt.hour().alias("hour"),
        pl.col("arrival_schedule").dt.weekday().alias("weekday"),
        pl.col("arrival_schedule").dt.month().alias("month"),
        pl.col("operating_date").dt.year().cast(pl.Int16).alias("year"),
        (
            pl.when(pl.col("arrival_schedule").dt.month().is_in([12, 1, 2])).then(pl.lit(1))
            .when(pl.col("arrival_schedule").dt.month().is_in([3, 4, 5])).then(pl.lit(2))
            .when(pl.col("arrival_schedule").dt.month().is_in([6, 7, 8])).then(pl.lit(3))
            .otherwise(pl.lit(4))
            .cast(pl.Int8).alias("season")   # 1=winter 2=spring 3=summer 4=fall
        ),
        (pl.col("arrival_schedule").dt.weekday() >= 5).alias("is_weekend"),
        # November anomaly flag — konsistent schlechtester Monat (F-TEMP-05)
        (pl.col("arrival_schedule").dt.month() == 11).alias("is_november"),
        # GTFS network epoch: Fahrplanwechsel Dez 2023 (F-NET-01, F-NET-03)
        pl.when(pl.col("operating_date") < pl.lit(date(2024, 1, 1)))
          .then(pl.lit("j23"))
          .otherwise(pl.lit("j24_j25"))
          .alias("gtfs_year"),
    ])


def add_interaction_features(frame):
    """Add interaction terms identified in analysis phase."""
    return frame.with_columns([
        # Event-Effekt primär Abend 18-22h (F-EVNT-03)
        (pl.col("event_weight") * pl.col("hour")).alias("event_weight_x_hour"),
        # Nacht-/Partyverkehr Fr/Sa 0-3h (F-TEMP-10)
        (pl.col("is_weekend") & pl.col("hour").is_in([0, 1, 2, 3])).alias("is_late_night_weekend"),
    ])
