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

# ─── 7. Route profile by direction (for dashboard direction filtering) ───────
print("Computing route_profile_by_direction...")

# Strategy: Use GTFS direction_id for authentic route directions
# Approach:
#   1. Get all unique (line_name, stop_name) pairs from test_final
#   2. Load GTFS trips and routes to find direction_id
#   3. Map direction_id back to our data

# First: Build mapping from route_short_name (line_name) to GTFS route_id
gtfs_routes_path = GTFS_DIR / "gtfs_tram_routes.parquet"
gtfs_trips_path = GTFS_DIR / "gtfs_tram_trips.parquet"

if gtfs_routes_path.exists() and gtfs_trips_path.exists():
    gtfs_routes_lf = pl.scan_parquet(gtfs_routes_path)
    routes_map = (
        gtfs_routes_lf
        .with_columns(pl.col("route_short_name").cast(pl.String))
        .select(["route_id", "route_short_name"])
        .collect()
        .to_dict(as_series=False)
    )
    route_short_to_id = {name: rid for name, rid in zip(routes_map["route_short_name"], routes_map["route_id"])}

    # Load GTFS trips to get direction_id per route_id
    gtfs_trips_lf = pl.scan_parquet(gtfs_trips_path)
    trips_directions = (
        gtfs_trips_lf
        .select(["route_id", "direction_id"])
        .unique()
        .collect()
    )

    # Build direction mapping: (line_name → [0, 1])
    available_directions_per_line = {}
    for row in trips_directions.iter_rows(named=True):
        route_id = row["route_id"]
        direction_id = row["direction_id"]

        # Find which line_name this route_id belongs to
        for line_name, rid in route_short_to_id.items():
            if rid == route_id:
                if line_name not in available_directions_per_line:
                    available_directions_per_line[line_name] = []
                if direction_id not in available_directions_per_line[line_name]:
                    available_directions_per_line[line_name].append(direction_id)

    # Now assign direction_id to all (line, stop) pairs
    line_direction_mapping = []
    test_lf = pl.scan_parquet(ROOT / "data" / "processed" / "test_final.parquet")

    for line_name in available_directions_per_line.keys():
        # Get all stops for this line
        stops_for_line = (
            test_lf
            .filter(pl.col("line_name") == line_name)
            .select("stop_name")
            .unique()
            .collect()["stop_name"].to_list()
        )

        # Each stop gets both directions (same stops, two directions)
        for direction_id in available_directions_per_line[line_name]:
            for stop_name in stops_for_line:
                line_direction_mapping.append((line_name, stop_name, direction_id))
else:
    # Fallback if GTFS not available: use simple sequence-based split
    print("  ⚠ GTFS routes not found, using fallback sequence-based directions")
    raw_lf = pl.scan_parquet(ROOT / "data" / "interim" / "train_raw.parquet")

    sequence_lookup = (
        raw_lf
        .with_columns(pl.col("line_name").cast(pl.String), pl.col("stop_name").cast(pl.String))
        .group_by(["line_name", "stop_name"])
        .agg(pl.col("stop_sequence").mode().first().alias("stop_sequence"))
        .collect()
    )

    line_direction_mapping = []
    for line_name, group in sequence_lookup.group_by("line_name"):
        sequences = group["stop_sequence"].to_list()
        if sequences:
            seq_mid = (min(sequences) + max(sequences)) / 2
            for row in group.iter_rows(named=True):
                dir_id = 1 if row["stop_sequence"] > seq_mid else 0
                line_direction_mapping.append((line_name, row["stop_name"], dir_id))

# Convert to DataFrame
direction_df = pl.DataFrame(
    line_direction_mapping,
    schema=["line_name", "stop_name", "direction_id"],
    orient="row"
).with_columns(
    pl.col("line_name").cast(pl.Categorical),
    pl.col("stop_name").cast(pl.Categorical),
)

# Step 2: Aggregate delays + coordinates by [line_name, direction_id, stop_name]
route_by_direction = (
    lf
    .join(direction_df.lazy(), on=["line_name", "stop_name"], how="inner")
    .group_by(["line_name", "direction_id", "stop_name"])
    .agg(
        pl.mean("arrival_delay").alias("mean_delay"),
        pl.quantile("arrival_delay", 0.9).alias("p90_delay"),
        (pl.col("arrival_delay").le(120).mean() * 100).alias("otp_pct"),
        pl.first("stop_lat").alias("lat"),
        pl.first("stop_lon").alias("lon"),
        pl.count().alias("n_obs"),
    )
    .collect()
    .with_columns(
        pl.col("stop_name").cast(pl.String),
        pl.col("line_name").cast(pl.String),
    )
    .sort(["line_name", "direction_id", "lat"])
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
