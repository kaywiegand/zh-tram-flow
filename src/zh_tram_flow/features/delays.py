"""Delay-derived features: delay_delta.

delay_delta = departure_delay - arrival_delay
  positive → delay grew at this stop (long dwell, heavy boarding)
  negative → delay recovered at this stop
  zero     → no change

delay_recovering (bool) is derivable on demand: delay_delta < 0
"""
import polars as pl


def add_delay_features(frame):
    """Add delay_delta as derived feature."""
    return frame.with_columns([
        (pl.col("departure_delay") - pl.col("arrival_delay")).alias("delay_delta"),
    ])
