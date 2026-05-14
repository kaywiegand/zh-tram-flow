"""
loader.py
---------
Raw data loading and year-splitting for the preparation pipeline.
"""
import polars as pl
from pathlib import Path

from wgnd.core._output import log, success
from zh_tram_flow.config import PATHS


def load_raw() -> pl.LazyFrame:
    """Scan master parquet as LazyFrame — no RAM until collect()."""
    path = PATHS["raw"] / "zh-tram-data-master.parquet"
    lf = pl.scan_parquet(path)
    schema = lf.collect_schema()
    n = lf.select(pl.len()).collect().item()
    date_min = lf.select(pl.col("operating_date").min()).collect().item()
    date_max = lf.select(pl.col("operating_date").max()).collect().item()
    log(f"{path.name}: {n:,} rows · {len(schema)} cols · {date_min} → {date_max}")
    return lf


def split_by_year(
    lf: pl.LazyFrame,
    years: list[str],
    out_dir: Path,
) -> dict[str, pl.LazyFrame]:
    """Split master LazyFrame into yearly parquet files.
    Returns dict of year → LazyFrame."""
    lazyframes = {}
    for year in years:
        path = out_dir / f"zh-tram-data-{year}.parquet"
        lf.filter(pl.col("operating_date").dt.year() == int(year)).sink_parquet(path)
        lazyframes[year] = pl.scan_parquet(path)
        n        = lazyframes[year].select(pl.len()).collect().item()
        date_min = lazyframes[year].select(pl.col("operating_date").min()).collect().item()
        date_max = lazyframes[year].select(pl.col("operating_date").max()).collect().item()
        log(f"  {year}: {n:,} rows  {date_min} → {date_max}")
    return lazyframes
