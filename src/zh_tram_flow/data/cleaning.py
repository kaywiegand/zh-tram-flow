"""
cleaning.py
-----------
Structural cleaning pipeline + meteo imputation for zh-tram-flow.

Call order in preparation pipeline:
  1. run_cleaning(lazyframes, years, out_dir)   — before split, no leakage
  2. run_preprocessing(out_train, ...)           — after split, train only
"""
import polars as pl
from pathlib import Path

from wgnd.core._output import log, warn, success

# ── Thresholds (from EDA) ────────────────────────────────────────────────────
DELAY_MAX_ABS = 3_600
BPUIC_MAX     = 100_000_000

METEO_COLS = [
    "temperature", "humidity", "rain_duration",
    "precipitation", "wind_speed", "global_radiation",
]

# ── Anomaly period: Nov 14 – Dec 23, 2025 ───────────────────────────────────
# departure_delay explodes in this window (avg +30s above arrival_delay).
# arrival_delay is unaffected and valid throughout.
# Cause: likely VBZ operational preparation for Dec 14 Fahrplanwechsel (j26).
# departure_delay and delay_delta are NOT model features → safe to NaN.
ANOMALY_START = pl.date(2025, 11, 14)
ANOMALY_END   = pl.date(2025, 12, 23)


# ── Individual cleaning steps ────────────────────────────────────────────────

def remove_duplicates(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.unique()

def filter_bpuic_anomalies(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.filter(pl.col("bpuic") <= BPUIC_MAX)

def filter_delay_mismatch(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.filter(
        pl.col("arrival_schedule").is_not_null() &
        pl.col("arrival_delay").is_not_null()
    )

def filter_extreme_delays(lf: pl.LazyFrame, max_abs: int = DELAY_MAX_ABS) -> pl.LazyFrame:
    return lf.filter(
        (pl.col("arrival_delay").abs() <= max_abs) &
        (pl.col("departure_delay").abs() <= max_abs)
    )

def clip_physical_bounds(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns(pl.col("humidity").clip(0, 100))

def fill_category_nulls(lf: pl.LazyFrame) -> pl.LazyFrame:
    schema = lf.collect_schema()
    exprs = []
    if "district_name" in schema:
        exprs.append(pl.col("district_name").fill_null("outside"))
    if "district_nr" in schema:
        exprs.append(pl.col("district_nr").fill_null(0).cast(pl.Int32))
    for col in ["event_name", "event_type", "event_location"]:
        if col in schema:
            exprs.append(pl.col(col).fill_null("no_event"))
    if "event_size" in schema:
        exprs.append(pl.col("event_size").fill_null(0))
    return lf.with_columns(exprs) if exprs else lf


# ── Full structural pipeline ─────────────────────────────────────────────────

def structural_cleaning_pipeline(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Structural cleaning — safe before train/test split. No leakage."""
    return (
        lf
        .pipe(remove_duplicates)
        .pipe(filter_bpuic_anomalies)
        .pipe(filter_delay_mismatch)
        .pipe(filter_extreme_delays)
        .pipe(clip_physical_bounds)
        .pipe(fill_category_nulls)
    )


# ── Anomaly masking ─────────────────────────────────────────────────────────

def mask_departure_anomaly(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Mask unplausible departure_delay / delay_delta values in Nov 14 – Dec 23 2025.

    arrival_delay is unaffected by the anomaly and remains valid.
    departure_delay and delay_delta are not model features — NaN-ing them
    preserves the full month coverage without contaminating predictions.

    Adds `is_anomal` flag (Bool) for transparency.
    """
    in_window = (
        (pl.col("operating_date") >= ANOMALY_START) &
        (pl.col("operating_date") <= ANOMALY_END)
    )
    schema = lf.collect_schema()
    exprs = [in_window.alias("is_anomal")]
    if "departure_delay" in schema:
        exprs.append(
            pl.when(in_window)
            .then(pl.lit(None, dtype=pl.Float64))
            .otherwise(pl.col("departure_delay"))
            .alias("departure_delay")
        )
    if "delay_delta" in schema:
        exprs.append(
            pl.when(in_window)
            .then(pl.lit(None, dtype=pl.Float64))
            .otherwise(pl.col("delay_delta"))
            .alias("delay_delta")
        )
    return lf.with_columns(exprs)


# ── lf_clean helper ──────────────────────────────────────────────────────────

def apply_lf_clean(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Standard analysis filter used across all notebooks.

    Removes structurally invalid records. Keeps Nov 14–Dec 23 2025 with
    departure_delay / delay_delta masked to NaN (arrival_delay is clean).

    Excludes:
    - canceled trips (no meaningful arrival_delay)
    - stop_sequence == 1 (terminus puffer artefact)
    - Linie E / L50 / L51 (structurally incomparable)
    """
    return (
        lf
        .filter(pl.col("canceled") == False)
        .filter(pl.col("stop_sequence") > 1)
        .filter(~pl.col("line_name").is_in(["E", "L50", "L51"]))
        .pipe(mask_departure_anomaly)
    )


# ── Post-split imputation ────────────────────────────────────────────────────

def impute_meteo_lazy(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Forward/backward fill meteo gaps — streaming, no collect()."""
    schema = lf.collect_schema()
    exprs = [
        pl.col(col).forward_fill().backward_fill()
        for col in METEO_COLS if col in schema
    ]
    lf = lf.sort("arrival_schedule").with_columns(exprs)
    if "flood_intensity" in schema:
        lf = lf.with_columns(pl.col("flood_intensity").fill_null(0))
    return lf


# ── Reporting ────────────────────────────────────────────────────────────────

def report_step(label: str, n_before: int, n_after: int) -> None:
    removed = n_before - n_after
    pct = removed / n_before * 100 if n_before > 0 else 0
    print(f"  {label:<45} {removed:>10,} removed  ({pct:.3f}%)  →  {n_after:,} remaining")


# ── Pipeline runner ──────────────────────────────────────────────────────────

def run_cleaning(
    lazyframes: dict,
    years: list[str],
    out_dir: Path,
) -> dict[str, Path]:
    """Run structural cleaning on all yearly files.
    Returns dict of year → cleaned parquet path."""
    clean_files = {}
    for year in years:
        out = out_dir / f"zh-tram-data-{year}-structural-clean.parquet"
        n_before = lazyframes[year].select(pl.len()).collect().item()
        log(f"\n{year} — before: {n_before:,} rows")
        structural_cleaning_pipeline(lazyframes[year]).sink_parquet(out)
        n_after = pl.scan_parquet(out).select(pl.len()).collect().item()
        report_step(f"Year {year}", n_before, n_after)
        success(f"Exported: {out.name}")
        clean_files[year] = out
    return clean_files
