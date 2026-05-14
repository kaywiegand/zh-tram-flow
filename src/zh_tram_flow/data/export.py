"""
export.py
---------
Feature engineering pipeline + parquet export.
"""
import polars as pl
from pathlib import Path

from wgnd.core._output import log, success
from zh_tram_flow.features.temporal import add_time_features
from zh_tram_flow.features.weather  import add_weather_flags
from zh_tram_flow.features.events   import add_event_features
from zh_tram_flow.features.delays   import add_delay_features


def run_export(
    out_train_prep: Path,
    out_test_prep: Path,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Run full feature engineering pipeline and export final parquets.
    Returns (out_train_feat, out_test_feat) paths."""
    out_train_feat = out_dir / "train_features.parquet"
    out_test_feat  = out_dir / "test_features.parquet"

    for inp, out in [(out_train_prep, out_train_feat), (out_test_prep, out_test_feat)]:
        (
            pl.scan_parquet(inp)
            .pipe(add_time_features)
            .pipe(add_weather_flags)
            .pipe(add_event_features)
            .pipe(add_delay_features)
            .sink_parquet(out)
        )

    n_train = pl.scan_parquet(out_train_feat).select(pl.len()).collect().item()
    n_test  = pl.scan_parquet(out_test_feat).select(pl.len()).collect().item()
    cols    = len(pl.scan_parquet(out_train_feat).collect_schema())

    success("Feature export complete.")
    log(f"  train: {n_train:,} rows · {cols} cols  →  {out_train_feat.name}")
    log(f"  test:  {n_test:,} rows · {cols} cols  →  {out_test_feat.name}")
    return out_train_feat, out_test_feat
