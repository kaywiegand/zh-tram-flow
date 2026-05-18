"""Network-based features: stop complexity, line complexity, start/end stop flags.

All features are computed from training data only (no leakage).
Use compute_network_stats() on train, then apply_network_features() on both train and test.

Features produced
-----------------
n_lines_at_stop : Int32
    Anzahl verschiedener Linien die diese Haltestelle bedienen.
    Hohe Werte → Knotenpunkt → höheres Kaskadenrisiko (F-SPAT-07, F-NET-05).

n_stops_line : Int32
    Anzahl verschiedener Haltestellen pro Linie (Linienlänge-Proxy).
    Alternative zu `gtfs_year` als kontinuierliches Netz-Feature (F-NET-03).

is_start_stop : Boolean
    Proxy-Flag für Starthaltestellen:
    avg_arrival_delay < THRESH_ARR und avg_delay_delta > THRESH_DELTA.
    Tram wartet an Starthaltestelle → kommt früh an, fährt pünktlich ab
    → grosse positive delay_delta → verzerrt Netzstatistik (F-SPAT-06).

is_end_stop : Boolean
    Proxy-Flag für Endhaltestellen (Terminus):
    avg_arrival_delay < THRESH_END und avg_delay_delta < THRESH_END_DELTA.
    Tram kommt früh an (eingebauter Puffer), kein nennenswertes Delta (F-SPAT-02, F-TARGET-02).
"""
import polars as pl

# Schwellenwerte — abgeleitet aus Spatial-Analyse (03_analysis_4-spatial)
THRESH_START_ARR   = -30   # Sekunden: Ankunft mindestens 30s vor Fahrplan
THRESH_START_DELTA = +20   # Sekunden: Abfahrts-Delta mindestens +20s (wartet, dann pünktlich)
THRESH_END_ARR     = -60   # Sekunden: Terminus kommt noch früher an
THRESH_END_DELTA   = +5    # Sekunden: kein grosses Delta (kein Warte-Effekt nötig)
MIN_OBS            = 200   # Mindest-Beobachtungen pro Haltestelle für verlässliche Schätzung


def compute_network_stats(lf_train: pl.LazyFrame) -> dict:
    """Compute aggregation-based network features from training data.

    Parameters
    ----------
    lf_train : pl.LazyFrame
        Preprocessed training data (after cleaning + imputation, before feature engineering).
        Must contain: stop_name, line_name, arrival_delay, departure_delay, canceled.

    Returns
    -------
    dict with keys:
        "stop_stats" : pl.DataFrame  — per-stop features (is_start_stop, is_end_stop, n_lines_at_stop)
        "line_stats" : pl.DataFrame  — per-line features (n_stops_line)
    """
    # delay_delta inline (not yet in preprocessed data)
    lf_noncanceled = (
        lf_train
        .filter(pl.col("canceled") == False)
        .with_columns(
            (pl.col("departure_delay") - pl.col("arrival_delay")).alias("_delta")
        )
    )

    # --- stop stats ---
    stop_agg = (
        lf_noncanceled
        .group_by("stop_name")
        .agg([
            pl.col("arrival_delay").mean().alias("_avg_arr"),
            pl.col("_delta").mean().alias("_avg_delta"),
            pl.len().alias("_n_obs"),
        ])
        .collect()
    )

    stop_lines = (
        lf_train
        .group_by("stop_name")
        .agg(pl.col("line_name").n_unique().cast(pl.Int32).alias("n_lines_at_stop"))
        .collect()
    )

    stop_stats = (
        stop_agg
        .join(stop_lines, on="stop_name", how="left")
        .with_columns([
            (
                (pl.col("_n_obs") >= MIN_OBS) &
                (pl.col("_avg_arr") < THRESH_START_ARR) &
                (pl.col("_avg_delta") > THRESH_START_DELTA)
            ).alias("is_start_stop"),
            (
                (pl.col("_n_obs") >= MIN_OBS) &
                (pl.col("_avg_arr") < THRESH_END_ARR) &
                (pl.col("_avg_delta") < THRESH_END_DELTA)
            ).alias("is_end_stop"),
        ])
        .select(["stop_name", "n_lines_at_stop", "is_start_stop", "is_end_stop",
                 "_avg_arr", "_avg_delta", "_n_obs"])
    )

    # --- line stats ---
    line_stats = (
        lf_train
        .group_by("line_name")
        .agg(pl.col("stop_name").n_unique().cast(pl.Int32).alias("n_stops_line"))
        .collect()
    )

    return {"stop_stats": stop_stats, "line_stats": line_stats}


def apply_network_features(frame: pl.LazyFrame, stop_stats: pl.DataFrame, line_stats: pl.DataFrame) -> pl.LazyFrame:
    """Join precomputed network stats to a LazyFrame.

    Parameters
    ----------
    frame : pl.LazyFrame
        Any frame with stop_name and line_name columns.
    stop_stats : pl.DataFrame
        Output of compute_network_stats()["stop_stats"].
    line_stats : pl.DataFrame
        Output of compute_network_stats()["line_stats"].

    Returns
    -------
    pl.LazyFrame with added network feature columns.
    """
    # Keep only the feature columns for joining (drop internal diagnostic cols)
    stop_join = stop_stats.select(["stop_name", "n_lines_at_stop", "is_start_stop", "is_end_stop"])
    line_join  = line_stats.select(["line_name", "n_stops_line"])

    return (
        frame
        .join(stop_join.lazy(), on="stop_name", how="left")
        .join(line_join.lazy(), on="line_name", how="left")
        # Fill unknown stops/lines (new in test, not seen in train) with neutral defaults
        .with_columns([
            pl.col("n_lines_at_stop").fill_null(1).cast(pl.Int32),
            pl.col("is_start_stop").fill_null(False),
            pl.col("is_end_stop").fill_null(False),
            pl.col("n_stops_line").fill_null(
                line_stats["n_stops_line"].median()
            ).cast(pl.Int32),
        ])
    )
