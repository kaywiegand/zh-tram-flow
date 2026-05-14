"""Event features: holiday flag, event flag, event weight."""
import polars as pl


def add_event_features(frame):
    """Add event-based features."""
    return frame.with_columns([
        (pl.col("event_type") == "Feiertag").alias("is_holiday"),
        pl.col("event_name").is_not_null().alias("has_event"),
        pl.col("event_size").fill_null(0).alias("event_weight"),    # 0=no event / 1/2/3
    ])
