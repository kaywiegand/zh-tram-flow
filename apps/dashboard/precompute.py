"""
precompute.py
-------------
One-time aggregation script: reads test_final.parquet (~29M rows) and writes
small aggregated tables to apps/dashboard/data/.

Run once before starting the dashboard:
    uv run python apps/dashboard/precompute.py

Output files (all in apps/dashboard/data/):
    stop_agg.parquet                 190 rows  — per-stop metrics
    hourly_agg.parquet               168 rows  — hour × weekday delay
    weather_agg.parquet               ~9 rows  — weather type × delay
    line_agg.parquet                  14 rows  — per-line metrics
    stop_line_lookup.parquet        1170 rows  — stop × line prediction features
    route_profile.parquet             190 rows  — spatial delay profile (line × stop)
    route_profile_by_direction.parquet ~380 rows — direction-specific profile (line × direction × stop) [NEW]
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# ─── Paths ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
GTFS_DIR = ROOT / "data" / "raw" / "gtfs"

# Use test_final for most aggregations (has all calculated features)
SRC_TEST = ROOT / "data" / "processed" / "test_final.parquet"
# But also load train_raw for direction mapping via terminus
SRC_RAW = ROOT / "data" / "interim" / "train_raw.parquet"

print(f"Reading {SRC_TEST} (for aggregations)...")
lf = pl.scan_parquet(SRC_TEST)

print(f"Reading {SRC_RAW} (for direction mapping)...")
lf_raw = pl.scan_parquet(SRC_RAW)

# ─── Direction mapping (via terminus: last stop of each trip) ────────────────
print("Building direction mapping from trip termini...")

# Step 1: Get terminus (last stop) per trip from raw data
terminus_mapping = (
    lf_raw
    .with_columns(pl.col("line_name").cast(pl.String))
    .group_by(["trip_id", "line_name"])
    .agg(
        pl.col("stop_name").sort_by("stop_sequence").last().alias("terminus"),  # ← MUST sort by sequence first!
    )
    .collect()
)

# Step 2: For each line, find the 2 most common termini (= the 2 directions)
direction_mapping = []
for line_name in terminus_mapping["line_name"].unique().to_list():
    line_termini = terminus_mapping.filter(pl.col("line_name") == line_name)
    # Count frequency of each terminus
    terminus_freq = (
        line_termini
        .group_by("terminus")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(2)
        .to_dicts()
    )

    for direction_id, term_dict in enumerate(terminus_freq):
        direction_mapping.append((line_name, term_dict["terminus"], direction_id))

direction_df_final = pl.DataFrame(
    direction_mapping,
    schema=["line_name", "terminus", "direction_id"],
    orient="row"
).with_columns(
    pl.col("line_name").cast(pl.Categorical),
    pl.col("terminus").cast(pl.Categorical),
)

print(f"  → Direction mapping: {len(direction_df_final)} terminus-direction pairs")

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

# ─── 6. Route delay profile with stop_sequence (for line geometry) ──────────
print("Computing route_profile with stop_sequence...")

# Step 1: Aggregate delays + coordinates from test_final
delay_data = (
    lf.group_by(["line_name", "stop_name"])
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.first("is_start_stop"),
        pl.first("is_end_stop"),
        pl.first("stop_lat").alias("lat"),
        pl.first("stop_lon").alias("lon"),
        pl.count().alias("n_obs"),
    )
    .collect()
    .with_columns(
        pl.col("stop_name").cast(pl.String),
        pl.col("line_name").cast(pl.String),
    )
)

# Step 2: Get stop_sequence from raw data (mode per line+stop)
# This gives us the typical sequencing for each stop on each line
raw_path = ROOT / "data" / "interim" / "train_raw.parquet"
raw_lf = pl.scan_parquet(raw_path)

sequence_lookup = (
    raw_lf
    .with_columns(pl.col("line_name").cast(pl.String), pl.col("stop_name").cast(pl.String))
    .group_by(["line_name", "stop_name"])
    .agg(pl.col("stop_sequence").mode().first().alias("stop_sequence"))
    .collect()
    .with_columns(
        pl.col("stop_name").cast(pl.String),
        pl.col("line_name").cast(pl.String),
    )
)

# Step 3: Merge and sort by sequence
# LEFT join: keep all stops from delay_data, match sequence if available
route_profile = (
    delay_data
    .join(sequence_lookup, on=["line_name", "stop_name"], how="left")
    .with_columns(
        # Replace NULL sequences with 9999 so they sort to the end
        pl.coalesce("stop_sequence", pl.lit(9999)).alias("_sort_seq"),
    )
    .sort(["line_name", "_sort_seq", "lat"])  # Primary: sequence; fallback: latitude
    .drop("_sort_seq")
)

route_profile.write_parquet(DATA_DIR / "route_profile.parquet")
print(f"  → route_profile: {len(route_profile)} rows")

print("Computing route_profile_by_direction...")

# Step: Aggregate delays by [line_name, direction_id, stop_name] using terminus-based directions
# Strategy:
#   1. From raw data: Get last stop (terminus) per trip
#   2. Map terminus to direction (0 or 1) via direction_df_final
#   3. Join back to test_final to get all delays per (trip, stop, direction)
#   4. Group by (line_name, direction_id, stop_name) and aggregate

# Get terminus per trip from raw data
trip_direction = (
    lf_raw
    .with_columns(pl.col("line_name").cast(pl.Categorical))
    .group_by("trip_id", "line_name")
    .agg(
        pl.col("stop_name").last().alias("terminus"),
    )
    .join(
        direction_df_final.lazy(),
        on=["line_name", "terminus"],
        how="left"
    )
    .drop("terminus")
    .collect()
)

# Get stop_sequence from raw data (test_final doesn't have it)
stop_sequence_lookup = (
    lf_raw
    .select(["trip_id", "stop_name", "stop_sequence"])
    .unique()
    .collect()
)

# Aggregate from test_final with direction mapping + stop_sequence
route_by_direction = (
    lf
    .with_columns(
        pl.col("line_name").cast(pl.Categorical),
        pl.col("stop_name").cast(pl.Categorical),
    )
    .join(
        trip_direction.lazy(),
        on="trip_id",
        how="left"
    )
    .filter(pl.col("direction_id").is_not_null())  # Only keep rows with mapped direction
    .join(
        stop_sequence_lookup.lazy(),
        on=["trip_id", "stop_name"],
        how="left"
    )
    .group_by(["line_name", "direction_id", "stop_name"])
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.quantile("arrival_delay", 0.9).alias("p90_delay"),
        (pl.col("arrival_delay").le(120).mean() * 100).alias("otp_pct"),
        pl.first("stop_lat").alias("lat"),
        pl.first("stop_lon").alias("lon"),
        pl.col("stop_sequence").mean().alias("stop_sequence"),  # ← Average per direction!
        pl.count().alias("n_obs"),
    )
    .collect()
    .with_columns(
        pl.col("stop_name").cast(pl.String),
        pl.col("line_name").cast(pl.String),
    )
    .sort(["line_name", "direction_id", pl.coalesce("stop_sequence", pl.lit(9999))])
)

route_by_direction.write_parquet(DATA_DIR / "route_profile_by_direction.parquet")
print(f"  → route_profile_by_direction: {len(route_by_direction)} rows")

print("\n✅ Precompute done. All files written to apps/dashboard/data/")
total_rows = (
    len(stop_agg) + len(hourly_agg) + len(weather_agg)
    + len(line_agg) + len(stop_line_lookup) + len(route_profile)
    + len(route_by_direction)
)
print(f"   Total rows loaded at dashboard startup: ~{total_rows:,} (vs. 29M raw)")
