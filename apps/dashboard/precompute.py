"""
precompute.py
-------------
One-time aggregation script: reads test_final.parquet (~29M rows) and writes
small aggregated tables to apps/dashboard/data/.

Run once before starting the dashboard:
    uv run python apps/dashboard/precompute.py

Output files (all in apps/dashboard/data/):
    stop_agg.parquet        190 rows  — per-stop metrics
    hourly_agg.parquet      168 rows  — hour × weekday delay
    weather_agg.parquet      ~9 rows  — weather type × delay
    line_agg.parquet         14 rows  — per-line metrics
    stop_line_lookup.parquet 1170 rows — stop × line prediction features
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# ─── Paths ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SRC = ROOT / "data" / "processed" / "test_final.parquet"

print(f"Reading {SRC} ...")
lf = pl.scan_parquet(SRC)

# ─── 1. Stop aggregation ─────────────────────────────────────────────────────
print("Computing stop_agg ...")

stop_agg = (
    lf.group_by("stop_name")
    .agg(
        pl.first("stop_lat").alias("lat"),
        pl.first("stop_lon").alias("lon"),
        pl.first("district_nr"),
        pl.first("n_lines_at_stop"),
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.quantile("arrival_delay", 0.9).alias("p90_delay"),
        (pl.col("arrival_delay").le(120).mean() * 100).alias("otp_pct"),
        pl.count().alias("n_obs"),
        pl.median("dwell_time").alias("dwell_time_median"),
    )
    .collect()
    .sort("mean_delay", descending=True)
)

stop_agg.write_parquet(DATA_DIR / "stop_agg.parquet")
print(f"  → stop_agg: {len(stop_agg)} rows")

# ─── 2. Hourly aggregation (hour × weekday) ───────────────────────────────────
print("Computing hourly_agg ...")

hourly_agg = (
    lf.group_by(["hour", "weekday"])
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.quantile("arrival_delay", 0.9).alias("p90_delay"),
        pl.count().alias("n_obs"),
    )
    .collect()
    .sort(["weekday", "hour"])
)

hourly_agg.write_parquet(DATA_DIR / "hourly_agg.parquet")
print(f"  → hourly_agg: {len(hourly_agg)} rows")

# ─── 3. Weather aggregation ──────────────────────────────────────────────────
print("Computing weather_agg ...")

# Build a single weather_type label from flags
weather_agg = (
    lf.with_columns(
        pl.when(pl.col("has_snow"))
        .then(pl.lit("Schnee"))
        .when(pl.col("has_heavy_rain"))
        .then(pl.lit("Starkregen"))
        .when(pl.col("has_rain"))
        .then(pl.lit("Regen"))
        .when(pl.col("is_hot"))
        .then(pl.lit("Hitze"))
        .otherwise(pl.lit("Kein Wettereinfluss"))
        .alias("weather_type")
    )
    .group_by("weather_type")
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.quantile("arrival_delay", 0.9).alias("p90_delay"),
        (pl.col("arrival_delay").le(120).mean() * 100).alias("otp_pct"),
        pl.count().alias("n_obs"),
    )
    .collect()
    .sort("mean_delay", descending=True)
)

weather_agg.write_parquet(DATA_DIR / "weather_agg.parquet")
print(f"  → weather_agg: {len(weather_agg)} rows")

# ─── 4. Line aggregation ─────────────────────────────────────────────────────
print("Computing line_agg ...")

line_agg = (
    lf.group_by("line_name")
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.quantile("arrival_delay", 0.9).alias("p90_delay"),
        (pl.col("arrival_delay").le(120).mean() * 100).alias("otp_pct"),
        pl.first("n_stops_line"),
        pl.count().alias("n_obs"),
    )
    .collect()
    .with_columns(pl.col("line_name").cast(pl.String))
    .sort("mean_delay", descending=True)
)

line_agg.write_parquet(DATA_DIR / "line_agg.parquet")
print(f"  → line_agg: {len(line_agg)} rows")

# ─── 5. Stop × line lookup (for prediction feature resolution) ───────────────
print("Computing stop_line_lookup ...")

stop_line_lookup = (
    lf.group_by(["stop_name", "line_name"])
    .agg(
        pl.first("district_nr"),
        pl.first("n_lines_at_stop"),
        pl.first("n_stops_line"),
        pl.first("is_start_stop"),
        pl.first("is_end_stop"),
        pl.median("dwell_time").alias("dwell_time_median"),
        pl.mean("arrival_delay").alias("mean_delay"),
    )
    .collect()
    .with_columns(
        pl.col("stop_name").cast(pl.String),
        pl.col("line_name").cast(pl.String),
    )
    .sort(["stop_name", "line_name"])
)

stop_line_lookup.write_parquet(DATA_DIR / "stop_line_lookup.parquet")
print(f"  → stop_line_lookup: {len(stop_line_lookup)} rows")

# ─── 6. Route delay profile (for cascade finding) ────────────────────────────
print("Computing route_profile ...")

# Stop sequence approximation: use mean delay along route, ordered by mean_delay
# for each line, group by stop to get the cascade profile
route_profile = (
    lf.group_by(["line_name", "stop_name"])
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.first("is_start_stop"),
        pl.first("is_end_stop"),
        pl.count().alias("n_obs"),
    )
    .collect()
    .with_columns(
        pl.col("stop_name").cast(pl.String),
        pl.col("line_name").cast(pl.String),
    )
    .sort(["line_name", "mean_delay"])
)

route_profile.write_parquet(DATA_DIR / "route_profile.parquet")
print(f"  → route_profile: {len(route_profile)} rows")

print("\n✅ Precompute done. All files written to apps/dashboard/data/")
total_rows = (
    len(stop_agg) + len(hourly_agg) + len(weather_agg)
    + len(line_agg) + len(stop_line_lookup) + len(route_profile)
)
print(f"   Total rows loaded at dashboard startup: ~{total_rows:,} (vs. 29M raw)")
