"""Delay-derived features: delay_delta, dwell_time.

delay_delta = departure_delay - arrival_delay
  positive → delay grew at this stop (long dwell, heavy boarding)
  negative → delay recovered at this stop
  zero     → no change

dwell_time = departure_schedule - arrival_schedule (in seconds)
  = geplante Aufenthaltszeit an der Haltestelle (F-TARGET-04)
  Kurze dwell_time → wenig Puffer → höheres Verspätungsrisiko (F-TARGET-03)

delay_recovering (bool) is derivable on demand: delay_delta < 0
"""
import polars as pl


def add_delay_features(frame):
    """Add delay_delta and dwell_time as derived features."""
    return frame.with_columns([
        (pl.col("departure_delay") - pl.col("arrival_delay")).alias("delay_delta"),
        # Geplante Haltezeit in Sekunden (F-TARGET-04)
        (pl.col("departure_schedule") - pl.col("arrival_schedule"))
            .dt.total_seconds()
            .cast(pl.Int32)
            .alias("dwell_time"),
    ])
