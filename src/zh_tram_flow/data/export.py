"""
export.py
---------
Feature engineering pipeline + parquet export.

Row-level features (no leakage risk, applied to both train and test independently):
  temporal : hour · weekday · month · season · is_weekend · is_rush_hour
             is_november · is_pre_july_2024 · gtfs_year
  weather  : has_rain · has_heavy_rain · is_windy · has_snow · has_flood · is_canceled · is_hot
  events   : is_holiday · has_event · event_weight
  delays   : delay_delta · dwell_time

Aggregation-based features (fit on train only, then applied to both — no leakage):
  network  : n_lines_at_stop · n_stops_line · is_start_stop · is_end_stop
"""
import polars as pl
from pathlib import Path

from wgnd.core._output import log, success
from zh_tram_flow.features.temporal import add_time_features
from zh_tram_flow.features.weather  import add_weather_flags
from zh_tram_flow.features.events   import add_event_features
from zh_tram_flow.features.delays   import add_delay_features
from zh_tram_flow.features.network  import compute_network_stats, apply_network_features


def run_export(
    out_train_prep: Path,
    out_test_prep: Path,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Run full feature engineering pipeline and export final parquets.

    Network stats (aggregation-based) are fit on train-prep only, then applied
    to both train and test — correct no-leakage approach.

    Returns (out_train_feat, out_test_feat) paths.
    """
    out_train_feat = out_dir / "train_features.parquet"
    out_test_feat  = out_dir / "test_features.parquet"

    # --- Step 1: compute network stats from train only ---
    log("Computing network stats from train data...")
    network_stats = compute_network_stats(pl.scan_parquet(out_train_prep))
    stop_stats = network_stats["stop_stats"]
    line_stats = network_stats["line_stats"]

    n_start = stop_stats["is_start_stop"].sum()
    n_end   = stop_stats["is_end_stop"].sum()
    log(f"  is_start_stop candidates : {n_start}")
    log(f"  is_end_stop   candidates : {n_end}")
    log(f"  n_lines_at_stop range    : {stop_stats['n_lines_at_stop'].min()}–{stop_stats['n_lines_at_stop'].max()}")
    log(f"  n_stops_line range       : {line_stats['n_stops_line'].min()}–{line_stats['n_stops_line'].max()}")

    # --- Step 2: apply all features to train + test ---
    for inp, out in [(out_train_prep, out_train_feat), (out_test_prep, out_test_feat)]:
        (
            pl.scan_parquet(inp)
            .pipe(add_time_features)
            .pipe(add_weather_flags)
            .pipe(add_event_features)
            .pipe(add_delay_features)
            .pipe(apply_network_features, stop_stats=stop_stats, line_stats=line_stats)
            .sink_parquet(out)
        )

    n_train = pl.scan_parquet(out_train_feat).select(pl.len()).collect().item()
    n_test  = pl.scan_parquet(out_test_feat).select(pl.len()).collect().item()
    cols    = len(pl.scan_parquet(out_train_feat).collect_schema())

    success("Feature export complete.")
    log(f"  train: {n_train:,} rows · {cols} cols  →  {out_train_feat.name}")
    log(f"  test:  {n_test:,} rows · {cols} cols  →  {out_test_feat.name}")
    return out_train_feat, out_test_feat
