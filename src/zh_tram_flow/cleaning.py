"""
cleaning.py
-----------
Cleaning-Pipeline für zh-tram-flow.

Aufruf-Reihenfolge:
  1. structural_cleaning_pipeline(lf)   — vor dem Split (kein Leakage-Risiko)
  2. impute_meteo_rolling(df)           — nach dem Split, erst auf Train

Alle strukturellen Funktionen arbeiten auf Polars LazyFrames.
impute_meteo_rolling arbeitet auf einem collect()ten DataFrame.
"""

import polars as pl

# ─── Schwellenwerte (aus EDA) ────────────────────────────────────────────────
DELAY_MAX_ABS  = 3_600        # |delay| > 1h → Datenfehler, kein Tramverkehr
BPUIC_MAX      = 100_000_000  # VBZ-IDs liegen im Bereich 8.5–8.6 Mio.

METEO_COLS = [
    "temperature", "humidity", "rain_duration",
    "precipitation", "wind_speed", "global_radiation",
]

# ─── Einzelne Cleaning-Schritte ──────────────────────────────────────────────

def remove_duplicates(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Entfernt vollständig duplizierte Zeilen (~1.72% laut EDA)."""
    return lf.unique()


def filter_bpuic_anomalies(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Entfernt Zeilen mit anomalen BPUIC-Werten > 100.000.000 (~0.10%)."""
    return lf.filter(pl.col("bpuic") <= BPUIC_MAX)


def filter_delay_mismatch(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Entfernt Zeilen ohne verwertbaren Delay-Wert für das Modell:
    - arrival_schedule IS NULL          → kein Zeitstempel, unbrauchbar
    - arrival_schedule OK, delay NULL   → Übertragungsfehler (~74.669 Zeilen laut EDA)
    """
    return lf.filter(
        pl.col("arrival_schedule").is_not_null() &
        pl.col("arrival_delay").is_not_null()
    )


def filter_extreme_delays(lf: pl.LazyFrame, max_abs: int = DELAY_MAX_ABS) -> pl.LazyFrame:
    """
    Entfernt Zeilen mit |delay| > max_abs Sekunden.
    Standardwert 3.600s (1h) — Tramverkehr hat keine plausiblen Abweichungen darüber.
    Betrifft < 0.01% der Zeilen laut EDA.
    """
    return lf.filter(
        (pl.col("arrival_delay").abs() <= max_abs) &
        (pl.col("departure_delay").abs() <= max_abs)
    )


def clip_physical_bounds(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Kappt physikalisch unmögliche Werte.
    humidity > 100%: Sensor-Kalibrierungsdrift, kein echter Fehler — nur clip nötig.
    """
    return lf.with_columns(
        pl.col("humidity").clip(0, 100)
    )


def fill_category_nulls(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Füllt kategoriale Nulls mit sinnvollen Default-Kategorien.
    - district_name/nr: Haltestellen außerhalb Stadtgebiet (6.87%)
    - event_*: Normalfall kein Event (78.5% null)
    """
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


# ─── Vollständige Pipeline ───────────────────────────────────────────────────

def structural_cleaning_pipeline(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Strukturelle Cleaning-Pipeline — sicher vor dem Train/Test-Split.
    Lernt keine statistischen Parameter → kein Leakage-Risiko.

    Reihenfolge:
      1. remove_duplicates
      2. filter_bpuic_anomalies
      3. filter_delay_mismatch
      4. filter_extreme_delays
      5. clip_physical_bounds
      6. fill_category_nulls
    """
    return (
        lf
        .pipe(remove_duplicates)
        .pipe(filter_bpuic_anomalies)
        .pipe(filter_delay_mismatch)
        .pipe(filter_extreme_delays)
        .pipe(clip_physical_bounds)
        .pipe(fill_category_nulls)
    )


# ─── Post-Split Cleaning ─────────────────────────────────────────────────────

def impute_meteo_lazy(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Lazy-Version der Meteo-Imputation — für sink_parquet ohne collect().
    Identische Logik wie impute_meteo_rolling, arbeitet aber auf LazyFrame.
    """
    schema = lf.collect_schema()
    exprs = [
        pl.col(col).forward_fill().backward_fill()
        for col in METEO_COLS
        if col in schema
    ]
    lf = lf.sort("arrival_schedule").with_columns(exprs)
    if "flood_intensity" in schema:
        lf = lf.with_columns(pl.col("flood_intensity").fill_null(0))
    return lf


def impute_meteo_rolling(df: pl.DataFrame) -> pl.DataFrame:
    """
    Füllt Meteo-Lücken via Forward/Backward Fill auf zeitlich sortierten Daten.
    Erst nach dem Split aufrufen — gleiche Funktion auf Train und Test anwenden
    (keine Parameter werden gelernt, Leakage-Risiko ist minimal).

    Strategie:
    - METEO_COLS: forward_fill → backward_fill (deckt kurze Stationsausfälle ab)
    - flood_intensity: fill_null(0) — Ereignis-Indikator, kein Mittelwert sinnvoll

    Warum Forward/Backward statt Rolling Mean?
    Das DataFrame enthält ~5.000 Trips pro Stunde. Ein Rolling Mean auf Trip-Ebene
    würde innerhalb einer Ausfallsstunde nur die ersten 2 Trips füllen (limit=2).
    Forward-Fill propagiert den letzten gültigen Stundenwert über alle Trips der
    Lückenstunde — das ist das korrekte Verhalten für stündlich gemessene Meteo-Daten.
    """
    result = df.sort("arrival_schedule").with_columns([
        pl.col(col).forward_fill().backward_fill()
        for col in METEO_COLS
        if col in df.columns
    ])

    if "flood_intensity" in df.columns:
        result = result.with_columns(
            pl.col("flood_intensity").fill_null(0)
        )

    return result


# ─── Reporting ───────────────────────────────────────────────────────────────

def report_step(label: str, n_before: int, n_after: int) -> None:
    """Gibt aus wie viele Zeilen ein Cleaning-Schritt entfernt hat."""
    removed = n_before - n_after
    pct = removed / n_before * 100 if n_before > 0 else 0
    print(f"  {label:<45} {removed:>10,} entfernt  ({pct:.3f}%)  →  {n_after:,} verbleiben")
