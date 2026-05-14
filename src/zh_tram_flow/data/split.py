"""
split.py
--------
Temporal train/test split: 2023+2024 → Train, 2025 → Test.
"""
import polars as pl
from pathlib import Path

from wgnd.core._output import log, success


def temporal_split(
    clean_files: dict,
    out_dir: Path,
) -> tuple[Path, Path]:
    """Temporal split into train (2023+2024) and test (2025).
    Returns (out_train, out_test) paths."""
    lf_train = pl.concat([
        pl.scan_parquet(clean_files["2023"]),
        pl.scan_parquet(clean_files["2024"]),
    ])
    lf_test = pl.scan_parquet(clean_files["2025"])

    n_2023  = pl.scan_parquet(clean_files["2023"]).select(pl.len()).collect().item()
    n_2024  = pl.scan_parquet(clean_files["2024"]).select(pl.len()).collect().item()
    n_test  = pl.scan_parquet(clean_files["2025"]).select(pl.len()).collect().item()
    n_train = n_2023 + n_2024
    n_total = n_train + n_test

    log(f"Train (2023+2024): {n_train:>12,}  ({n_train/n_total*100:.1f}%)")
    log(f"  2023:            {n_2023:>12,}")
    log(f"  2024:            {n_2024:>12,}")
    log(f"Test  (2025):      {n_test:>12,}  ({n_test/n_total*100:.1f}%)")

    out_train = out_dir / "train_raw.parquet"
    out_test  = out_dir / "test_raw.parquet"
    lf_train.sink_parquet(out_train)
    lf_test.sink_parquet(out_test)
    success(f"Split exported → {out_dir.name}/")
    return out_train, out_test
