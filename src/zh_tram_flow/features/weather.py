"""Weather condition flags: rain, heavy rain, wind, snow, flood, temperature."""
import polars as pl


def add_weather_flags(frame):
    """Add weather-based boolean flags."""
    return frame.with_columns([
        (pl.col("precipitation") > 0).alias("has_rain"),
        (pl.col("precipitation") > 5.0).alias("has_heavy_rain"),
        (
            (pl.col("precipitation") > 0) & (pl.col("temperature") < 2)
        ).alias("has_snow"),
        (pl.col("flood_intensity") > 0).alias("has_flood"),
        # Hohe Temperaturen verursachen mehr Verspätung als Kälte (F-WEAT-04)
        (pl.col("temperature") > 20).alias("is_hot"),
    ])
