"""
preprocessing.py
----------------
Post-split preprocessing: meteo imputation.
Fit on train only — apply identically to test (no learned parameters → no leakage).
"""
import polars as pl
from pathlib import Path

from wgnd.core._output import log, warn, success
from zh_tram_flow.data.cleaning import impute_meteo_lazy, METEO_COLS


def run_preprocessing(
    out_train: Path,
    out_test: Path,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Meteo imputation via forward/backward fill on train and test.
    Returns (out_train_prep, out_test_prep) paths."""
    out_train_prep = out_dir / "train_prepared.parquet"
    out_test_prep  = out_dir / "test_prepared.parquet"

    null_check = (
        pl.scan_parquet(out_train)
        .select(METEO_COLS)
        .select([pl.col(c).null_count().alias(c) for c in METEO_COLS])
        .collect()
    )
    log("Train — nulls before imputation:")
    for col in METEO_COLS:
        n = null_check[col][0]
        if n > 0:
            warn(f"  {col:<25} {n:>8,} nulls")

    print()
    log("Running imputation on train...")
    impute_meteo_lazy(pl.scan_parquet(out_train)).sink_parquet(out_train_prep)
    log("Running imputation on test ...")
    impute_meteo_lazy(pl.scan_parquet(out_test)).sink_parquet(out_test_prep)
    success("Preprocessing complete.")
    return out_train_prep, out_test_prep
