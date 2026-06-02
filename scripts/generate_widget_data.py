"""
Generate prediction lookup data for the live-prediction HTML widget.

Loads lgbm_v1 (schedule-only, no live prev_trip_delay signal needed),
pre-computes predictions for all (stop, line) pairs × hour × day_type × weather,
and outputs the JSON structure to stdout (to be embedded in live-prediction.html).

Usage:
    uv run python scripts/generate_widget_data.py > /tmp/widget_data.json
    # or
    uv run python scripts/generate_widget_data.py --embed  # writes HTML directly
"""

import json
import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import lightgbm as lgb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO = Path(__file__).parents[1]
MODEL_PATH  = REPO / "data" / "models" / "lgbm_v1.txt"
META_PATH   = REPO / "data" / "models" / "lgbm_v1_meta.json"
DATA_PATH   = REPO / "data" / "processed" / "test_final.parquet"
OUTPUT_HTML = REPO / "reports" / "live-prediction.html"


# ---------------------------------------------------------------------------
# Load model & meta
# ---------------------------------------------------------------------------

def load_model():
    booster = lgb.Booster(model_file=str(MODEL_PATH))
    with open(META_PATH) as f:
        meta = json.load(f)
    return booster, meta


# ---------------------------------------------------------------------------
# Extract stop-line features from parquet
# ---------------------------------------------------------------------------

def get_stop_line_features(features: list[str]) -> pd.DataFrame:
    """Return one row per (stop_name, line_name) with stable stop-level features."""
    cols = [
        "stop_name", "line_name", "district_nr",
        "n_lines_at_stop", "n_stops_line",
        "is_start_stop", "is_end_stop", "dwell_time",
    ]
    lf = pl.scan_parquet(DATA_PATH).select(cols)

    df = (
        lf.group_by(["stop_name", "line_name"])
        .agg([
            pl.col("district_nr").mode().first().alias("district_nr"),
            pl.col("n_lines_at_stop").mode().first().alias("n_lines_at_stop"),
            pl.col("n_stops_line").mode().first().alias("n_stops_line"),
            pl.col("is_start_stop").mode().first().alias("is_start_stop"),
            pl.col("is_end_stop").mode().first().alias("is_end_stop"),
            pl.col("dwell_time").median().alias("dwell_time"),
        ])
        .sort(["stop_name", "line_name"])
        .collect()
        .to_pandas()
    )
    return df


# ---------------------------------------------------------------------------
# Weather scenario definitions
# ---------------------------------------------------------------------------

WEATHER_SCENARIOS = {
    "normal": dict(
        temperature=15.0, precipitation=0.0, wind_speed=5.0,
        has_rain=False, has_heavy_rain=False, has_snow=False,
        has_flood=False, is_hot=False, flood_intensity=0,
    ),
    "rain": dict(
        temperature=13.0, precipitation=5.0, wind_speed=9.0,
        has_rain=True, has_heavy_rain=False, has_snow=False,
        has_flood=False, is_hot=False, flood_intensity=0,
    ),
    "snow": dict(
        temperature=-2.0, precipitation=3.0, wind_speed=6.0,
        has_rain=False, has_heavy_rain=False, has_snow=True,
        has_flood=False, is_hot=False, flood_intensity=0,
    ),
}

# Fixed context: typical June weekday / Sunday
DAY_TYPE_BASE = {
    "weekday": dict(
        weekday=2,        # Wednesday
        is_weekend=False,
        month=6, season="summer", year=2024, gtfs_year="j24",
        is_november=False,
    ),
    "weekend": dict(
        weekday=6,        # Sunday
        is_weekend=True,
        month=6, season="summer", year=2024, gtfs_year="j24",
        is_november=False,
    ),
}

# Fixed event context: no event
EVENT_BASE = dict(
    event_type="no_event", event_size=0, has_event=False,
    event_weight=0, is_holiday=False,
)


# ---------------------------------------------------------------------------
# Build feature rows
# ---------------------------------------------------------------------------

def build_feature_rows(stop_line_df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, list]:
    """
    For each (stop, line) pair × 24 hours × 2 day_types × 3 weather scenarios,
    build a feature row matching the model's feature set.

    Returns:
        rows_df:  wide DataFrame with all feature rows
        index:    list of (stop, line, day_type, weather, hour) tuples
    """
    all_rows = []
    index = []

    for _, stop_row in stop_line_df.iterrows():
        stop   = stop_row["stop_name"]
        line   = stop_row["line_name"]

        for day_type, day_base in DAY_TYPE_BASE.items():
            for weather, wx in WEATHER_SCENARIOS.items():
                for hour in range(24):
                    is_late_night_weekend = bool(
                        day_base["is_weekend"] and hour in (0, 1, 2, 3)
                    )
                    event_weight_x_hour = 0  # no event

                    row = {
                        # Stop / line identifiers
                        "line_name":      line,
                        "stop_name":      stop,
                        "district_nr":    stop_row["district_nr"],
                        # Weather
                        **wx,
                        # Event (none)
                        **EVENT_BASE,
                        # Temporal
                        "hour":           hour,
                        **day_base,
                        # Derived
                        "is_late_night_weekend": is_late_night_weekend,
                        "event_weight_x_hour":   event_weight_x_hour,
                        # Stop-level schedule features
                        "dwell_time":       stop_row["dwell_time"],
                        "n_lines_at_stop":  stop_row["n_lines_at_stop"],
                        "n_stops_line":     stop_row["n_stops_line"],
                        "is_start_stop":    stop_row["is_start_stop"],
                        "is_end_stop":      stop_row["is_end_stop"],
                    }
                    all_rows.append(row)
                    index.append((stop, line, day_type, weather, hour))

    rows_df = pd.DataFrame(all_rows)

    # Enforce correct dtypes for categoricals
    cat_cols = ["line_name", "stop_name", "event_type", "season", "gtfs_year"]
    for col in cat_cols:
        if col in rows_df.columns:
            rows_df[col] = rows_df[col].astype("category")

    # Boolean → int8 (LightGBM prefers int)
    bool_cols = [
        "is_weekend", "is_november", "has_rain", "has_heavy_rain",
        "has_snow", "has_flood", "is_hot", "is_holiday", "has_event",
        "is_start_stop", "is_end_stop", "is_late_night_weekend",
    ]
    for col in bool_cols:
        if col in rows_df.columns:
            rows_df[col] = rows_df[col].astype("int8")

    # Select and order features exactly as trained
    rows_df = rows_df[features]
    return rows_df, index


# ---------------------------------------------------------------------------
# Build output JSON structure
# ---------------------------------------------------------------------------

def build_json(stop_line_df: pd.DataFrame, predictions: np.ndarray, index: list) -> dict:
    """
    Structure:
    {
      "stops": [...],
      "stop_lines": {"stop": ["line", ...]},
      "predictions": {
        "stop": {
          "line": {
            "weekday": {"normal": [p0..p23], "rain": [...], "snow": [...]},
            "weekend": {...}
          }
        }
      }
    }
    """
    result: dict = {}

    for pred, (stop, line, day_type, weather, hour) in zip(predictions, index):
        result.setdefault(stop, {})
        result[stop].setdefault(line, {})
        result[stop][line].setdefault(day_type, {})
        result[stop][line][day_type].setdefault(weather, [None] * 24)
        result[stop][line][day_type][weather][hour] = round(float(pred), 1)

    stop_lines: dict = {}
    for stop in sorted(result.keys()):
        stop_lines[stop] = sorted(result[stop].keys())

    return {
        "stops": sorted(result.keys()),
        "stop_lines": stop_lines,
        "predictions": result,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate widget prediction data.")
    parser.add_argument("--embed", action="store_true",
                        help="Write output directly into reports/live-prediction.html")
    args = parser.parse_args()

    print("Loading model...", file=sys.stderr)
    booster, meta = load_model()
    features = meta["features"]
    print(f"  Features: {len(features)}", file=sys.stderr)

    print("Extracting stop-line features...", file=sys.stderr)
    stop_line_df = get_stop_line_features(features)
    n_pairs = len(stop_line_df)
    n_rows  = n_pairs * 24 * 2 * 3
    print(f"  {n_pairs} (stop, line) pairs → {n_rows:,} prediction rows", file=sys.stderr)

    print("Building feature matrix...", file=sys.stderr)
    rows_df, index = build_feature_rows(stop_line_df, features)

    print("Predicting...", file=sys.stderr)
    preds = booster.predict(rows_df)
    preds = np.clip(preds, 0, 600)  # cap at 600s for display

    print("Building JSON...", file=sys.stderr)
    data = build_json(stop_line_df, preds, index)

    json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    size_kb  = len(json_str.encode()) / 1024
    print(f"  JSON size: {size_kb:.1f} KB", file=sys.stderr)

    if args.embed:
        # Read the HTML template and embed the JSON
        html_path = OUTPUT_HTML
        if not html_path.exists():
            print(f"ERROR: {html_path} not found. Run without --embed first.", file=sys.stderr)
            sys.exit(1)
        content = html_path.read_text()
        # Replace the placeholder
        new_content = content.replace(
            "/* WIDGET_DATA_PLACEHOLDER */",
            f"const WIDGET_DATA = {json_str};"
        )
        html_path.write_text(new_content)
        print(f"✅ Embedded {size_kb:.1f} KB JSON into {html_path}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
