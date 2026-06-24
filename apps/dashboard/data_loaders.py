"""
Single Source of Truth für Streckenplan-Daten im Dashboard.
Alle Views basieren auf dieser einen Funktion.
"""

import polars as pl
import pandas as pd
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "processed"
GTFS_DIR = ROOT / "data" / "raw" / "gtfs"


def get_line_profile(
    line_name: str,
    direction_id: int | None = None,
    year: str = "2025",
    route_dir_df: pl.DataFrame | None = None,
    stop_df: pl.DataFrame | None = None,
) -> Dict[str, Any]:
    """
    Single Source of Truth für eine Tram-Linie und Fahrtrichtung.

    Args:
        line_name: z.B. "11"
        direction_id: 0 oder 1 (GTFS direction_id), oder None für "Gesamt (beide)"
        year: "2023", "2024", "2025"
        route_dir_df: vorberechnete `route_profile_by_direction.parquet` (optional, wird geladen falls None)
        stop_df: vorberechnete `stop_agg.parquet` (optional, wird geladen falls None)

    Returns:
        {
            'line_name': str,
            'direction_id': int | None,
            'direction_label': str,  # z.B. "Richtung A: Oerlikon → Central"
            'stops': pd.DataFrame mit:
                - stop_sequence (int)
                - stop_name (str)
                - lat, lon (float)
                - mean_delay (float)
                - otp_pct (float)
                - dwell_time_median (float)
                - n_obs (int)
            'shape_geom': pd.DataFrame mit:
                - lat, lon (float) — für Karte (sortiert nach sequence)
        }
    """

    # ─────────────────────────────────────────────────────────────────
    # 0. Lade Daten falls nicht bereitgestellt
    # ─────────────────────────────────────────────────────────────────

    if route_dir_df is None:
        try:
            route_dir_df = pl.read_parquet(Path(__file__).parent / "data" / "route_profile_by_direction.parquet")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"route_profile_by_direction.parquet nicht gefunden. "
                f"Bitte zuerst ausführen: uv run python apps/dashboard/precompute.py"
            )

    if stop_df is None:
        try:
            stop_df = pl.read_parquet(Path(__file__).parent / "data" / "stop_agg.parquet")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"stop_agg.parquet nicht gefunden. "
                f"Bitte zuerst ausführen: uv run python apps/dashboard/precompute.py"
            )

    # ─────────────────────────────────────────────────────────────────
    # 1. Lade Stops für diese Linie + Richtung
    # ─────────────────────────────────────────────────────────────────

    route_filter = route_dir_df.filter(pl.col("line_name").cast(pl.String) == str(line_name))

    if direction_id is not None:
        route_stops = route_filter.filter(pl.col("direction_id") == direction_id)
    else:
        # Gesamt: dir=0 stops + echte dir=1-exklusive Stops (Einbahnstraßen)
        # Normalisierung vor Vergleich: gleiche Gleis-Plattformen (Bellevue A/B/C/D)
        # nicht als unterschiedliche Stops zählen
        _norm = (
            pl.col("stop_name")
            .str.replace(r"^Zürich, ?", "", literal=False)
            .str.replace(r" [A-F]$", "", literal=False)
        )
        dir0 = route_filter.filter(pl.col("direction_id") == 0).with_columns(_norm.alias("_norm"))
        dir1 = route_filter.filter(pl.col("direction_id") == 1).with_columns(_norm.alias("_norm"))
        stops_in_dir0_norm = set(dir0["_norm"].to_list())
        extra = dir1.filter(~pl.col("_norm").is_in(stops_in_dir0_norm)).drop("_norm")
        route_stops = pl.concat([dir0.drop("_norm"), extra])

    if len(route_stops) == 0:
        raise ValueError(f"Keine Halte gefunden für L{line_name} Richtung {direction_id}")

    # Daten aus route_profile_by_direction.parquet sind bereits geografisch geordnet
    # Keine zusätzliche Sortierung nötig

    # Konvertiere zu Pandas (für Dashboard-Kompatibilität)
    # route_profile_by_direction enthält seit Rebuild alle Metriken direkt (normalisierter Join)
    base_cols = ["stop_name", "lat", "lon"]
    if "stop_sequence" in route_stops.columns:
        base_cols.insert(0, "stop_sequence")

    # Metriken aus dem Parquet nutzen falls vorhanden
    metric_cols = [c for c in ["mean_delay", "otp_pct", "dwell_time_median"] if c in route_stops.columns]
    all_cols = base_cols + metric_cols

    stops_df = route_stops.select(all_cols).to_pandas()

    # Nur wenn Metriken fehlen (z.B. ältere Parquet-Version): Fallback auf stop_df-Join
    missing = [c for c in ["mean_delay", "otp_pct", "dwell_time_median"] if c not in stops_df.columns]
    if missing and stop_df is not None:
        stop_metrics = stop_df.select(["stop_name"] + missing).to_pandas()
        stops_df = stops_df.merge(stop_metrics, on="stop_name", how="left")

    stops_df["mean_delay"] = stops_df.get("mean_delay", 0.0) if "mean_delay" in stops_df.columns else 0.0
    if "mean_delay" in stops_df.columns:
        stops_df["mean_delay"] = stops_df["mean_delay"].fillna(0.0)
    if "otp_pct" in stops_df.columns:
        stops_df["otp_pct"] = stops_df["otp_pct"].fillna(87.0)
    else:
        stops_df["otp_pct"] = 87.0
    if "dwell_time_median" in stops_df.columns:
        stops_df["dwell_time_median"] = stops_df["dwell_time_median"].fillna(0.0)
    else:
        stops_df["dwell_time_median"] = 0.0

    # n_obs: alle Stops gleichwertig (tramlines_stops hat keine IST-Frequenz)
    stops_df["n_obs"] = len(stops_df)

    # Erstelle stop_short für Dashboard-Kompatibilität (entfernt "Zürich, " Prefix)
    stops_df["stop_short"] = stops_df["stop_name"].str.replace(r"Zürich, ?", "", regex=True)

    # ─────────────────────────────────────────────────────────────────
    # 2. Lade Shape-Geometrie (für Karte) — GTFS
    # ─────────────────────────────────────────────────────────────────

    shape_geom = _load_shape_geometry(str(line_name), direction_id or 0, year)

    # ─────────────────────────────────────────────────────────────────
    # 3. Erstelle Fahrtrichtungs-Label
    # ─────────────────────────────────────────────────────────────────

    if len(stops_df) > 0:
        start_stop = stops_df["stop_name"].iloc[0].replace("Zürich, ", "")
        end_stop = stops_df["stop_name"].iloc[-1].replace("Zürich, ", "")

        if direction_id is None:
            direction_label = f"Gesamt (beide Richtungen): L{line_name}"
        else:
            dir_letter = chr(65 + direction_id)  # A=65, B=66
            direction_label = f"Richtung {dir_letter}: {start_stop} → {end_stop}"
    else:
        direction_label = f"L{line_name}"

    # ─────────────────────────────────────────────────────────────────
    # 4. Rückgabe
    # ─────────────────────────────────────────────────────────────────

    return {
        'line_name': line_name,
        'direction_id': direction_id,
        'direction_label': direction_label,
        'stops': stops_df,
        'shape_geom': shape_geom,
    }


def get_direction_choices(
    line_name: str,
    year: str = "2025",
    route_dir_df: pl.DataFrame | None = None,
) -> list[tuple[int, str]]:
    """
    Welche Fahrtrichtungen gibt es für diese Linie?

    Returns: [(direction_id, label), ...]
    Beispiel: [(0, "Richtung A: Flughafen → Zürich"), (1, "Richtung B: ...")]
    """

    if route_dir_df is None:
        try:
            route_dir_df = pl.read_parquet(Path(__file__).parent / "data" / "route_profile_by_direction.parquet")
        except FileNotFoundError:
            return []

    directions = (
        route_dir_df
        .filter(pl.col("line_name").cast(pl.String) == str(line_name))
        .select(["direction_id", "stop_name"])
        .unique()
        .sort("direction_id")
        .to_pandas()
    )

    if len(directions) == 0:
        return []

    choices = []
    for dir_id in sorted(directions["direction_id"].unique()):
        # Finde Start und End Stop für diese Richtung
        dir_id_int = int(dir_id)  # Ensure Python int, not numpy type
        dir_df_sorted = route_dir_df.filter(
            (pl.col("line_name").cast(pl.String) == str(line_name)) &
            (pl.col("direction_id") == dir_id_int)
        ).to_pandas()

        if len(dir_df_sorted) > 0:
            # Daten sind bereits in geografischer Reihenfolge aus precompute.py
            start_stop = dir_df_sorted["stop_name"].iloc[0].replace("Zürich, ", "")
            end_stop = dir_df_sorted["stop_name"].iloc[-1].replace("Zürich, ", "")
            dir_letter = chr(65 + int(dir_id_int))
            label = f"Richtung {dir_letter}: {start_stop} → {end_stop}"
            choices.append((int(dir_id_int), label))

    return choices


def _load_shape_geometry(line_name: str, direction_id: int = 0, year: str = "2025") -> pd.DataFrame:
    """
    Lade GTFS shape coordinates für eine Linie + Richtung.

    Returns: DataFrame mit [lat, lon] (sortiert nach shape_pt_sequence)
    """
    try:
        trips = pl.read_parquet(GTFS_DIR / "gtfs_tram_trips.parquet")
        routes = pl.read_parquet(GTFS_DIR / "gtfs_tram_routes.parquet")
        shapes = pl.read_parquet(GTFS_DIR / "gtfs_tram_shapes.parquet")
    except FileNotFoundError:
        return pd.DataFrame(columns=["lat", "lon"])

    # Finde dominante shape_id für diese Linie + Richtung + Jahr
    dominant = (
        trips
        .join(
            routes.select(["route_id", "route_short_name", "year"]),
            on=["route_id", "year"]
        )
        .filter(
            (pl.col("route_short_name") == str(line_name)) &
            (pl.col("direction_id") == direction_id) &
            (pl.col("year") == year)
        )
        .group_by("shape_id")
        .agg(pl.len().alias("n_trips"))
        .sort("n_trips", descending=True)
        .head(1)
    )

    if len(dominant) == 0:
        return pd.DataFrame(columns=["lat", "lon"])

    shape_id = dominant["shape_id"][0]

    return (
        shapes
        .filter((pl.col("shape_id") == shape_id) & (pl.col("year") == year))
        .sort("shape_pt_sequence")
        .select([
            pl.col("shape_pt_lat").alias("lat"),
            pl.col("shape_pt_lon").alias("lon"),
        ])
        .to_pandas()
    )
