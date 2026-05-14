"""Temporal features: hour, weekday, month, season, is_weekend, is_rush_hour."""
import polars as pl


def add_time_features(frame):
    """Add time-based features from arrival_schedule."""
    return frame.with_columns([
        pl.col("arrival_schedule").dt.hour().alias("hour"),
        pl.col("arrival_schedule").dt.weekday().alias("weekday"),
        pl.col("arrival_schedule").dt.month().alias("month"),
        (
            pl.when(pl.col("arrival_schedule").dt.month().is_in([12, 1, 2])).then(pl.lit(1))
            .when(pl.col("arrival_schedule").dt.month().is_in([3, 4, 5])).then(pl.lit(2))
            .when(pl.col("arrival_schedule").dt.month().is_in([6, 7, 8])).then(pl.lit(3))
            .otherwise(pl.lit(4))
            .cast(pl.Int8).alias("season")   # 1=winter 2=spring 3=summer 4=fall
        ),
        (pl.col("arrival_schedule").dt.weekday() >= 5).alias("is_weekend"),
        pl.col("arrival_schedule").dt.hour().is_in([7, 8, 9, 17, 18, 19]).alias("is_rush_hour"),
    ])
