"""
Zurich Tram Flow — Explorer Dashboard v2
Drei interaktive Tools für Stakeholder nach der Präsentation.
Starten: uv run streamlit run apps/dashboard/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import streamlit as st
import numpy as np
import sys
from pathlib import Path

# Streamlit lädt vom apps/dashboard/-Verzeichnis, also path anpassen
sys.path.insert(0, str(Path(__file__).parent))
from data_loaders import get_line_profile, get_direction_choices

# ─── Pfade ────────────────────────────────────────────────────────────────────

ROOT   = Path(__file__).resolve().parent.parent.parent
AGG    = Path(__file__).resolve().parent / "data"
MODELS = ROOT / "data" / "models"
GTFS_DIR = ROOT / "data" / "raw" / "gtfs"

# ─── Konstanten ───────────────────────────────────────────────────────────────

NAVY  = "#1a3a5c"
BLUE  = "#2E86AB"
GREEN = "#27ae60"
AMBER = "#e67e22"
RED   = "#e74c3c"
MUTED = "#718096"

LINE_COLORS = {
    "2": "#E20A16", "3": "#00892F", "4": "#11296F", "5": "#9B59B6",
    "6": "#CA7D3C", "7": "#000000", "8": "#8AB51F", "9": "#11296F",
    "10": "#E12472", "11": "#00892F", "12": "#92D6E3", "13": "#FFCC00",
    "14": "#008DC5", "15": "#E20A16", "17": "#8E224D",
    "50": "#888888", "51": "#888888",
}

WEEKDAY_LABELS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

OTP_TARGET = 95.0

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Zurich Tram Flow — Explorer",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
section[data-testid="stSidebar"] { background: #1a3a5c; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] .stRadio label { font-size: 1rem; padding: 0.35rem 0; }
.block-container { padding-top: 3rem; max-width: 1200px; }

.page-title   { font-size: 1.7rem; font-weight: 800; color: #1a3a5c; margin-bottom: 0.2rem; }
.page-sub     { font-size: 0.97rem; color: #718096; margin-bottom: 1.5rem; line-height: 1.55; }

.insight-box  {
    background: #eef6fb; border-left: 5px solid #2E86AB;
    padding: 0.9rem 1.3rem; border-radius: 6px;
    font-size: 0.95rem; color: #1a3a5c; margin: 1rem 0;
}
.rec-box {
    background: #f0fff4; border-left: 5px solid #27ae60;
    padding: 0.9rem 1.3rem; border-radius: 6px;
    font-size: 0.95rem; color: #1a4a2a; margin: 1rem 0;
}
.warn-box {
    background: #fff8ec; border-left: 5px solid #e67e22;
    padding: 0.9rem 1.3rem; border-radius: 6px;
    font-size: 0.95rem; color: #7d4e0f; margin: 1rem 0;
}
.error-box {
    background: #fff5f5; border-left: 5px solid #e74c3c;
    padding: 0.9rem 1.3rem; border-radius: 6px;
    font-size: 0.95rem; color: #7d2a1f; margin: 1rem 0;
}
.pred-box { padding: 1.4rem 2rem; border-radius: 8px; margin: 0.8rem 0; text-align: center; }
.pred-green { background: #f0fff4; border: 2px solid #27ae60; }
.pred-amber { background: #fffbeb; border: 2px solid #e67e22; }
.pred-red   { background: #fff5f5; border: 2px solid #e74c3c; }
.pred-val   { font-size: 3rem; font-weight: 800; line-height: 1.1; }
.pred-green .pred-val { color: #27ae60; }
.pred-amber .pred-val { color: #e67e22; }
.pred-red   .pred-val { color: #e74c3c; }
.pred-lbl   { font-size: 0.9rem; color: #718096; margin-top: 0.3rem; }

.section-label {
    font-size: 0.75rem; font-weight: 700; color: #2E86AB;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Daten (gecacht) ──────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_data():
    stop   = pl.read_parquet(AGG / "stop_agg.parquet")
    line   = pl.read_parquet(AGG / "line_agg.parquet")
    route  = pl.read_parquet(AGG / "route_profile.parquet")
    route_dir = pl.read_parquet(AGG / "route_profile_by_direction.parquet")
    lookup = pl.read_parquet(AGG / "stop_line_lookup.parquet")
    return stop, line, route, route_dir, lookup

@st.cache_resource(show_spinner=False)
def load_model():
    m = lgb.Booster(model_file=str(MODELS / "lgbm_v1.txt"))
    with open(MODELS / "lgbm_v1_meta.json") as f:
        meta = json.load(f)
    return m, meta

stop_df, line_df, route_df, route_dir_df, lookup_df = load_data()

# Hilfslisten
ALL_LINES = sorted(
    line_df["line_name"].cast(pl.String).unique().to_list(),
    key=lambda x: int(x) if x.isdigit() else 99,
)

# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def box(text: str, kind: str = "insight") -> None:
    css = {"insight": "insight-box", "rec": "rec-box", "warn": "warn-box", "error": "error-box"}[kind]
    st.markdown(f'<div class="{css}">{text}</div>', unsafe_allow_html=True)

def recommendation_box_color(otp: float) -> str:
    """Bestimmt Box-Klasse für Handlungsempfehlung basierend auf OTP."""
    if otp >= 92:
        return "rec"      # Grün — über Netzschnitt
    elif otp >= 87:
        return "warn"     # Orange — moderater Handlungsbedarf
    else:
        return "error"    # Rot — hoher Handlungsbedarf

def section_label(text: str) -> None:
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)

def line_color(ln: str) -> str:
    return LINE_COLORS.get(str(ln), BLUE)

def otp_delta_str(otp: float) -> str:
    gap = otp - OTP_TARGET
    return f"{gap:+.1f} PP zum Ziel"

@st.cache_data(show_spinner=False)
def load_gtfs_shapes(line: str) -> pd.DataFrame:
    """Load GTFS shape (track geometry) for a line.

    Returns: DataFrame with columns [lat, lon] in sequence order.
    Falls back to empty DataFrame if GTFS files not found.
    """
    try:
        trips_lf = pl.scan_parquet(GTFS_DIR / "gtfs_tram_trips.parquet")
        routes_lf = pl.scan_parquet(GTFS_DIR / "gtfs_tram_routes.parquet")
        shapes_lf = pl.scan_parquet(GTFS_DIR / "gtfs_tram_shapes.parquet")
    except FileNotFoundError:
        return pd.DataFrame(columns=["lat", "lon"])

    # Dominant shape per line: most trips, direction=1, latest year
    dominant = (
        trips_lf
        .join(routes_lf.select(["route_id", "route_short_name", "year"]),
              on=["route_id", "year"])
        .filter(pl.col("route_short_name") == str(line))
        .filter(pl.col("direction_id") == 1)
        .group_by(["route_short_name", "shape_id"])
        .agg(pl.len().alias("n_trips"))
        .sort("n_trips", descending=True)
        .collect()
        .select("shape_id")
        .head(1)
    )

    if len(dominant) == 0:
        return pd.DataFrame(columns=["lat", "lon"])

    shape_id = dominant["shape_id"][0]

    return (
        shapes_lf
        .filter(pl.col("shape_id") == shape_id)
        .sort("shape_pt_sequence")
        .select([
            pl.col("shape_pt_lat").alias("lat"),
            pl.col("shape_pt_lon").alias("lon"),
        ])
        .collect()
        .to_pandas()
    )

def filter_route_for_display(route: pd.DataFrame, threshold_pct: float = 0.05) -> pd.DataFrame:
    """Filter stops to main route (≥threshold% of max frequency).

    Removes variant stops that appear in <5% of main-route trips.
    Used consistently in both map and bar chart.
    """
    if len(route) == 0 or "n_obs" not in route.columns:
        return route

    max_n = route["n_obs"].max()
    return route[route["n_obs"] >= max_n * threshold_pct].copy()

def plot_line_map_with_geometry(line: str, route: pd.DataFrame, shape_geom: pd.DataFrame | None = None) -> go.Figure:
    """Karte mit echtem Linienzug (GTFS Shape) + gefilterten Haltestellen.

    Logik:
    1. GTFS Shapes laden oder nutzen bereitgestellte shape_geom (echte Gleisgeometrie)
    2. Route stops filtern: nur ≥5% der Hauptroute-Frequenz (entfernt Varianten)
    3. Bubble-Größe power-skaliert (2-24px, nicht linear)
    4. Zwei Layer: Linienzug (Tramfarbe) + Blasen (Delay-Farbcodierung)
    """
    # Layer 1: GTFS Shape (echte Gleisgeometrie)
    # Nutze bereitgestelltes shape_geom falls vorhanden, sonst lade es
    if shape_geom is not None and len(shape_geom) > 0:
        shapes = shape_geom.copy()
    else:
        shapes = load_gtfs_shapes(line)

    # Layer 2: Filter route to main stops (consistent with bar chart)
    if len(route) > 0:
        route_copy = route.copy()  # Bereits gefiltert wenn es von get_line_profile() kommt

        # Bubble-Größe: power-scaled mit Mindestgröße für Sichtbarkeit
        if len(route_copy) > 0 and "mean_delay" in route_copy.columns:
            delays = route_copy["mean_delay"].values
            d_min, d_max = float(np.nanmin(delays)), float(np.nanmax(delays))
            norm = (delays - d_min) / (d_max - d_min + 1e-9)
            route_copy["bubble"] = 8 + (norm ** 1.5) * 18  # power-scaled, 8-26px (min visible)
        else:
            route_copy["bubble"] = 10
    else:
        route_copy = pd.DataFrame()

    # Erstelle Figure
    fig = go.Figure()
    line_color_val = line_color(line)

    # Layer 1: Linienzug (GTFS Shape)
    if len(shapes) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=shapes["lat"],
            lon=shapes["lon"],
            mode="lines",
            line=dict(width=3, color=line_color_val),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Layer 2: Haltestellen-Blasen (gefiltert + power-scaled)
    if len(route_copy) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=route_copy["lat"],
            lon=route_copy["lon"],
            mode="markers",
            marker=dict(
                size=route_copy["bubble"],
                color=route_copy.get("mean_delay", 0),
                colorscale=[[0, GREEN], [0.4, AMBER], [1, RED]],
                colorbar=dict(title="Verspätung (s)", thickness=12),
            ),
            text=[
                f"<b>{stop}</b><br>Ø Verspätung: {delay:.1f}s<br>OTP: {otp:.1f}%"
                for stop, delay, otp in zip(
                    route_copy.get("stop_name", []),
                    route_copy.get("mean_delay", []),
                    route_copy.get("otp_pct", []),
                )
            ],
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        ))

    # Configure map
    center_lat = (
        shapes["lat"].mean() if len(shapes) > 0
        else route_copy["lat"].mean() if len(route_copy) > 0
        else 47.37
    )
    center_lon = (
        shapes["lon"].mean() if len(shapes) > 0
        else route_copy["lon"].mean() if len(route_copy) > 0
        else 8.54
    )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=11.5,
        ),
        margin=dict(r=0, t=0, l=0, b=0),
        height=440,
        hovermode="closest",
    )

    return fig

def route_for_line_and_direction(line: str, direction_id: int | None = None) -> pd.DataFrame:
    """Route-Profil einer Linie und Fahrtrichtung.

    Falls direction_id ist int (0 oder 1): nur diese Richtung
    Falls direction_id=None (Gesamt): Halte von Richtung 0, aber Metriken aus stop_df (alle Richtungen kombiniert)

    Wichtig: Sortierung nach stop_sequence pro Richtung:
      - Richtung 0: ASC (Start→Ende)
      - Richtung 1: DESC (Ende→Start — umgekehrte Sequenz)
      - Gesamt: ASC (Richtung 0 Reihenfolge)
    """
    r = route_dir_df.filter(pl.col("line_name").cast(pl.String) == str(line))

    if direction_id is not None:
        r = r.filter(pl.col("direction_id") == direction_id)
    else:
        # Gesamt: Nutze Richtung 0 als Basis-Reihenfolge (Start→Ende)
        r = r.filter(pl.col("direction_id") == 0)

    r = (
        r
        .with_columns(pl.col("stop_name").cast(pl.Utf8))
        .join(
            stop_df.select(["stop_name", "mean_delay", "otp_pct", "dwell_time_median"])
                .with_columns(pl.col("stop_name").cast(pl.Utf8)),
            on="stop_name", how="left",
        )
    )

    # Sort by stop_sequence (primary) with fallback to lat if NULL
    # For direction 1, reverse the sequence (Ende→Start)
    if direction_id == 1:
        r = r.sort(pl.coalesce("stop_sequence", pl.lit(9999)), descending=True)
    else:
        r = r.sort(pl.coalesce("stop_sequence", pl.lit(9999)), descending=False)

    r = r.to_pandas()
    r["stop_short"] = r["stop_name"].str.replace(r"Zürich, ?", "", regex=True)
    return r

def route_for_line(line: str) -> pd.DataFrame:
    """Route-Profil einer Linie — sortiert nach stop_sequence (direction=0, GTFS-kanonisch).

    route_df (route_profile.parquet) enthält alle Metriken bereits nach normalisiertem Join
    mit stop_agg. Kein weiterer stop_df-Join nötig.
    """
    r = (
        route_df
        .filter(pl.col("line_name").cast(pl.String) == str(line))
        .with_columns(pl.col("stop_name").cast(pl.Utf8))
        .to_pandas()
    )
    # Fallback: join with stop_df if metrics missing (e.g. old parquet version)
    if "otp_pct" not in r.columns or r["otp_pct"].isna().all():
        stop_metrics = stop_df.select(["stop_name", "otp_pct", "dwell_time_median"]).to_pandas()
        stop_metrics["stop_name"] = stop_metrics["stop_name"].str.replace(r"^Zürich, ?", "", regex=True)
        r = r.merge(stop_metrics, on="stop_name", how="left")
    r["stop_short"] = r["stop_name"].str.replace(r"Zürich, ?", "", regex=True)
    return r

def worst_stops_for_line(line: str, n: int = 5) -> pd.DataFrame:
    return (
        lookup_df
        .filter(pl.col("line_name").cast(pl.String) == str(line))
        .with_columns(pl.col("stop_name").cast(pl.Utf8))
        .join(stop_df.select(["stop_name", "mean_delay", "otp_pct", "dwell_time_median"])
                .with_columns(pl.col("stop_name").cast(pl.Utf8)),
              on="stop_name", how="left")
        .sort("mean_delay", descending=True)
        .head(n)
        .select(["stop_name", "mean_delay", "otp_pct", "dwell_time_median"])
        .rename({
            "stop_name": "Haltestelle",
            "mean_delay": "Ø Verspätung (s)",
            "otp_pct": "OTP (%)",
            "dwell_time_median": "Puffer (s)",
        })
        .with_columns([
            pl.col("Ø Verspätung (s)").round(1),
            pl.col("OTP (%)").round(1),
            pl.col("Puffer (s)").round(0).cast(pl.Int32),
        ])
        .to_pandas()
    )

def line_stats(line: str) -> dict:
    row = line_df.filter(pl.col("line_name").cast(pl.String) == str(line))
    if len(row) == 0:
        return {}
    return row.row(0, named=True)

def recommendation_text(line: str, stats: dict, worst: pd.DataFrame) -> str:
    """Erzeugt eine datenbasierte Handlungsempfehlung für die gewählte Linie."""
    otp   = stats.get("otp_pct", 0.0)
    delay = stats.get("mean_delay", 0.0)
    gap   = OTP_TARGET - otp

    # Haltestellen ohne Puffer und hohem Delay
    no_buffer = worst[worst["Puffer (s)"] == 0]
    n_no_buf  = len(no_buffer)

    if otp >= 92:
        return (
            f"<strong>Linie {line} liegt über Netzschnitt</strong> (OTP {otp:.1f}%). "
            f"Kein akuter Handlungsbedarf. Monitoring der {n_no_buf} Haltestellen ohne Puffer empfohlen."
        )
    elif otp >= 87:
        return (
            f"<strong>Linie {line} — moderater Handlungsbedarf.</strong> "
            f"OTP {otp:.1f}% · Lücke {gap:.1f} PP. "
            f"{n_no_buf} der 5 schlechtesten Haltestellen haben 0s Fahrplanpuffer. "
            f"Empfehlung: +20–30s an den Problemhalten einplanen."
        )
    else:
        worst_stop = worst.iloc[0]["Haltestelle"] if len(worst) > 0 else "—"
        worst_stop_short = str(worst_stop).replace("Zürich, ", "")
        return (
            f"<strong>Linie {line} — hoher Handlungsbedarf.</strong> "
            f"OTP {otp:.1f}% · Ø Delay {delay:.0f}s · Lücke {gap:.1f} PP zum Ziel. "
            f"Schlechteste Haltestelle: <em>{worst_stop_short}</em>. "
            f"{n_no_buf} Haltestellen ohne eingebauten Puffer. "
            f"Fahrplan-Redesign mit +30–45s Puffer an den Top-3-Problemhalten empfohlen."
        )

MONTH_TO_SEASON = {12:1,1:1,2:1, 3:2,4:2,5:2, 6:3,7:3,8:3, 9:4,10:4,11:4}

def build_feature_row(line_name, stop_name, hour, weekday, month,
                      temperature, has_rain, has_snow, is_holiday, has_event) -> pd.DataFrame:
    row_data = lookup_df.filter(
        (pl.col("stop_name") == stop_name) & (pl.col("line_name").cast(pl.String) == str(line_name))
    )
    if len(row_data) == 0:
        district_nr = n_lines_at_stop = 1
        dwell_time = n_stops_line = 20
        is_start_stop = is_end_stop = False
    else:
        r = row_data.row(0, named=True)
        district_nr      = r["district_nr"]
        n_lines_at_stop  = r["n_lines_at_stop"]
        dwell_time       = int(r["dwell_time_median"] or 0)
        n_stops_line     = r["n_stops_line"]
        is_start_stop    = r["is_start_stop"]
        is_end_stop      = r["is_end_stop"]

    season                = MONTH_TO_SEASON[month]
    is_weekend            = weekday >= 5
    event_weight          = 3 if has_event else 0
    is_late_night_weekend = is_weekend and (hour >= 22 or hour <= 4)

    row = {
        "line_name": line_name, "stop_name": stop_name,
        "district_nr": district_nr, "temperature": float(temperature),
        "precipitation": 2.0 if has_rain else 0.0, "wind_speed": 5.0,
        "flood_intensity": 0, "event_type": "Konzert" if has_event else "no_event",
        "event_size": 3 if has_event else 0, "hour": hour, "weekday": weekday,
        "month": month, "year": 2025, "season": season, "is_weekend": is_weekend,
        "is_november": month == 11, "gtfs_year": "j24_j25",
        "has_rain": has_rain, "has_heavy_rain": False, "has_snow": has_snow,
        "has_flood": False, "is_hot": temperature >= 30, "is_holiday": is_holiday,
        "has_event": has_event, "event_weight": event_weight,
        "dwell_time": dwell_time, "n_lines_at_stop": n_lines_at_stop,
        "n_stops_line": n_stops_line, "is_start_stop": is_start_stop,
        "is_end_stop": is_end_stop, "event_weight_x_hour": event_weight * hour,
        "is_late_night_weekend": is_late_night_weekend,
    }
    df = pd.DataFrame([row])
    for col in ["line_name", "stop_name", "event_type", "season", "gtfs_year"]:
        df[col] = df[col].astype("category")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 0.5rem">
        <div style="font-size:1rem;font-weight:600">Zurich Tram Flow</div>
        <div style="font-size:1.25rem;font-weight:800;margin-top:0.15rem">Dashboard-Prototype</div>
        <div style="font-size:0.78rem;opacity:0.6;margin-top:0.3rem">
            Data VBZ 2023–2025
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Tool",
        ["Linie erkunden", "Linien vergleichen", "Verspätung vorhersagen"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem;opacity:0.55;line-height:1.6">
        Projekt-Informationen:<br>
        <a href="https://github.com/kaywiegand/zh-tram-flow"
           target="_blank"
           style="color:inherit;text-decoration:underline">
            GitHub: zh-tram-flow
        </a>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEITE 1 — LINIE ERKUNDEN
# ══════════════════════════════════════════════════════════════════════════════

if page == "Linie erkunden":
    st.markdown('<div class="page-title">Linie erkunden</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">'
        'Wo entstehen Verspätungen — und auf welchen Linien ist der Handlungsbedarf am grössten? '
        'Basierend auf 94 Mio. VBZ-Fahrten 2023–2025.<br><br>'
        'Alle Werte sind Durchschnitte über den Gesamtzeitraum.<br><br>'
        'Dieser erste Prototyp soll die Möglichkeiten der weiteren Verwendung der gesammelten Erkenntnisse aufzeigen. '
        'Dabei ist zu beachten, dass die Daten nicht primär für diese Darstellung aufbereitet wurden und durch eine '
        'Vielzahl an Änderungen des Strecken- und Fahrplans im Zeitraum 2023–2025 und Inkonsistenzen der '
        'Haltestellenbenennung die Ansichten zu visuellen Abweichungen führen können.<br><br>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Dropdown + 3 KPIs in einer Zeile ──
    col_sel, col_otp, col_delay, col_stops = st.columns(4, gap="large")

    with col_sel:
        sel_line = st.selectbox(
            "Linie wählen",
            ALL_LINES,
            index=ALL_LINES.index("11") if "11" in ALL_LINES else 0,
            format_func=lambda x: f"Linie {x}",
        )

    # Daten laden
    try:
        profile = get_line_profile(sel_line, direction_id=None, route_dir_df=route_dir_df, stop_df=stop_df)
    except Exception as e:
        st.error(f"Fehler beim Laden des Linienprofils: {e}")
        st.stop()

    stops_df = profile['stops']
    shape_geom = profile['shape_geom']

    if len(stops_df) == 0:
        st.warning("Keine Daten für diese Linie.")
        st.stop()

    route_filtered = filter_route_for_display(stops_df)

    n_stops = len(route_filtered)
    otp = route_filtered["otp_pct"].mean() if "otp_pct" in route_filtered.columns else 0.0
    delay = route_filtered["mean_delay"].mean() if "mean_delay" in route_filtered.columns else 0.0

    worst = route_filtered.nlargest(5, "mean_delay") if len(route_filtered) > 0 else pd.DataFrame()
    if len(worst) > 0:
        worst_display = worst[["stop_name", "mean_delay", "otp_pct", "dwell_time_median"]].copy()
        worst_display.columns = ["Haltestelle", "Ø Verspätung (s)", "OTP (%)", "Puffer (s)"]
        worst = worst_display
    else:
        worst = pd.DataFrame(columns=["Haltestelle", "Ø Verspätung (s)", "OTP (%)", "Puffer (s)"])

    col_otp.metric(
        "Pünktlichkeit (OTP)",
        f"{otp:.1f}%",
        delta=otp_delta_str(otp),
        delta_color="normal",
    )
    col_delay.metric("Ø Verspätung", f"{delay:.0f}s")
    col_stops.metric("Haltestellen", int(n_stops))

    st.markdown("---")

    # ── Delay-Profil: Plotly Bar (nach Delay sortiert) ──
    section_label("Verspätung pro Haltestelle")

    # route_filtered already calculated above — use it consistently
    color = line_color(sel_line)
    bar_colors = [RED if d > 70 else AMBER if d > 40 else color for d in route_filtered["mean_delay"]]

    fig_route = go.Figure(go.Bar(
        x=route_filtered["stop_short"],
        y=route_filtered["mean_delay"].round(1),
        marker_color=bar_colors,
        marker_line_width=0,
        marker_line_color="rgba(0,0,0,0)",  # Transparent outline
        text=route_filtered["mean_delay"].round(0).astype(int).astype(str) + "s",
        textposition="outside",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Ø Verspätung: %{y:.1f}s<br>"
            "OTP: %{customdata[1]:.1f}%<br>"
            "Puffer: %{customdata[2]:.0f}s"
            "<extra></extra>"
        ),
        customdata=list(zip(
            route_filtered["stop_name"],
            route_filtered["otp_pct"].fillna(0),
            route_filtered["dwell_time_median"].fillna(0),
        )),
    ))
    fig_route.add_hline(
        y=delay, line_dash="dash", line_color=MUTED,
        annotation_text=f"Linien-Ø {delay:.0f}s",
        annotation_position="top right",
    )
    fig_route.add_hline(
        y=56, line_dash="dot", line_color="#aaa",
        annotation_text="Netz-Ø 56s",
        annotation_position="bottom right",
    )
    fig_route.update_layout(
        height=360,
        margin=dict(t=30, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(tickangle=-40, tickfont=dict(size=10), showgrid=False),
        yaxis=dict(gridcolor="#eee", title="Ø Verspätung (s)", zeroline=False),
        showlegend=False,
        hovermode="x unified",
    )
    st.plotly_chart(fig_route, use_container_width=True)

    # ── Karte: Echte Linienzug-Geometrie (GTFS) + gefilterte Blasen ──
    st.markdown("---")
    section_label("Karte — Linienzug mit Verspätungen")

    fig_map = plot_line_map_with_geometry(sel_line, route_filtered, shape_geom=shape_geom)
    st.plotly_chart(fig_map, use_container_width=True)

    # ── Top-5 Problemhaltestellen ──
    st.markdown("---")
    section_label("Rangliste der Haltestellenverspätungen")

    # worst is already filtered to main route (calculated above) — use directly
    col_tbl, col_rec = st.columns([3, 2], gap="large")

    with col_tbl:
        st.dataframe(
            worst,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Ø Verspätung (s)": st.column_config.NumberColumn(format="%.1f s"),
                "OTP (%)": st.column_config.NumberColumn(format="%.1f %%"),
                "Puffer (s)": st.column_config.NumberColumn(format="%d s"),
            },
        )

    with col_rec:
        rec_text = recommendation_text(sel_line, {"otp_pct": otp, "mean_delay": delay}, worst)
        box(rec_text, kind=recommendation_box_color(otp))

    box(
        f"Tipp: Im Tab <strong>«Verspätung vorhersagen»</strong> kannst du für jede Haltestelle "
        f"dieser Linie konkrete Szenarien durchspielen — z.B. was Schnee oder ein Event kostet.",
        kind="insight",
    )


# ══════════════════════════════════════════════════════════════════════════════
# SEITE 2 — LINIEN VERGLEICHEN
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Linien vergleichen":
    st.markdown('<div class="page-title">Linien vergleichen</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Zwei Linien direkt gegenüberstellen — '
        'OTP, Delay-Verteilung, schlechteste Haltestellen.</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        line_a = st.selectbox(
            "Linie A",
            ALL_LINES,
            index=ALL_LINES.index("11") if "11" in ALL_LINES else 0,
            format_func=lambda x: f"Linie {x}",
            key="cmp_a",
        )
    with col_b:
        default_b = ALL_LINES.index("4") if "4" in ALL_LINES else 1
        line_b = st.selectbox(
            "Linie B",
            ALL_LINES,
            index=default_b,
            format_func=lambda x: f"Linie {x}",
            key="cmp_b",
        )

    # Get routes and filter to main-route stops
    route_a = route_for_line(line_a)
    route_b = route_for_line(line_b)
    route_a_filtered = filter_route_for_display(route_a)
    route_b_filtered = filter_route_for_display(route_b)

    # Calculate stats from filtered routes only
    def calc_stats(route_filtered):
        """Calculate OTP, delays, stop count from route."""
        if len(route_filtered) == 0:
            return {"otp_pct": 0, "mean_delay": 0, "p90_delay": 0, "n_stops_line": 0}
        return {
            "otp_pct": route_filtered["otp_pct"].mean(),
            "mean_delay": route_filtered["mean_delay"].mean(),
            "p90_delay": route_filtered["mean_delay"].quantile(0.9),
            "n_stops_line": len(route_filtered),
        }

    stats_a = calc_stats(route_a_filtered)
    stats_b = calc_stats(route_b_filtered)

    # Calculate worst stops for both lines (filtered to main route)
    worst_a = route_a_filtered.nlargest(5, "mean_delay") if len(route_a_filtered) > 0 else pd.DataFrame()
    worst_b = route_b_filtered.nlargest(5, "mean_delay") if len(route_b_filtered) > 0 else pd.DataFrame()

    # Prepare display format for both
    if len(worst_a) > 0:
        worst_a_display = worst_a[["stop_name", "mean_delay", "otp_pct", "dwell_time_median"]].copy()
        worst_a_display.columns = ["Haltestelle", "Ø Verspätung (s)", "OTP (%)", "Puffer (s)"]
        worst_a = worst_a_display
    else:
        worst_a = pd.DataFrame(columns=["Haltestelle", "Ø Verspätung (s)", "OTP (%)", "Puffer (s)"])

    if len(worst_b) > 0:
        worst_b_display = worst_b[["stop_name", "mean_delay", "otp_pct", "dwell_time_median"]].copy()
        worst_b_display.columns = ["Haltestelle", "Ø Verspätung (s)", "OTP (%)", "Puffer (s)"]
        worst_b = worst_b_display
    else:
        worst_b = pd.DataFrame(columns=["Haltestelle", "Ø Verspätung (s)", "OTP (%)", "Puffer (s)"])

    st.markdown("---")

    # ── KPI-Vergleich ──
    section_label("Kennzahlen im Vergleich (Hauptroute)")

    kpi_cols = st.columns(4)
    def kpi_pair(col, label, val_a, val_b, fmt="{:.1f}", suffix="", inverse=False):
        better_a = val_a > val_b if not inverse else val_a < val_b
        col.markdown(f"**{label}**")
        col.markdown(
            f"<span style='color:{line_color(line_a)};font-size:1.4rem;font-weight:700'>"
            f"L{line_a}: {fmt.format(val_a)}{suffix}</span>",
            unsafe_allow_html=True,
        )
        col.markdown(
            f"<span style='color:{line_color(line_b)};font-size:1.4rem;font-weight:700'>"
            f"L{line_b}: {fmt.format(val_b)}{suffix}</span>",
            unsafe_allow_html=True,
        )
        winner = line_a if better_a else line_b
        col.caption(f"Besser: Linie {winner}")

    kpi_pair(kpi_cols[0], "OTP",
             stats_a["otp_pct"], stats_b["otp_pct"], suffix="%")
    kpi_pair(kpi_cols[1], "Ø Verspätung",
             stats_a["mean_delay"], stats_b["mean_delay"],
             fmt="{:.0f}", suffix="s", inverse=True)
    kpi_pair(kpi_cols[2], "P90 Verspätung",
             stats_a["p90_delay"], stats_b["p90_delay"],
             fmt="{:.0f}", suffix="s", inverse=True)
    kpi_pair(kpi_cols[3], "Haltestellen",
             stats_a["n_stops_line"], stats_b["n_stops_line"],
             fmt="{:.0f}", inverse=True)

    st.markdown("---")

    # ── Overlapping Bar Chart — normalized width ──
    section_label("Verspätungs-Verteilung — Hauptroute beider Linien")

    fig_cmp = go.Figure()
    for route, ln, lw in [(route_a_filtered, line_a, 3.0), (route_b_filtered, line_b, 2.0)]:
        if len(route) > 0:
            # Normalize x positions to [0, 100] for comparable visual width
            x_norm = np.linspace(0, 100, len(route))
            fig_cmp.add_trace(go.Scatter(
                name=f"Linie {ln}",
                x=x_norm,
                y=route["mean_delay"].round(1),
                mode="lines+markers",
                line=dict(color=line_color(ln), width=lw),
                marker=dict(size=6, color=line_color(ln)),
                hovertemplate=(
                    f"<b>Linie {ln}</b><br>%{{customdata}}<br>"
                    "Ø Verspätung: %{y:.1f}s<extra></extra>"
                ),
                customdata=route["stop_short"],
            ))

    fig_cmp.add_hline(y=56, line_dash="dot", line_color="#aaa",
                      annotation_text="Netz-Ø 56s", annotation_position="top left")
    fig_cmp.update_layout(
        height=340,
        margin=dict(t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="Strecke (normalisiert von Start zu Ende)", showgrid=False, zeroline=False),
        yaxis=dict(gridcolor="#eee", title="Ø Verspätung (s)", zeroline=False),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(255,255,255,0.8)", bordercolor="#ccc", borderwidth=1
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    # ── Top-5 nebeneinander ──
    st.markdown("---")
    section_label("Rangliste der Haltestellenverspätungen")

    col_wa, col_wb = st.columns(2, gap="large")
    with col_wa:
        st.caption(f"Linie {line_a}")
        st.dataframe(worst_a, hide_index=True, use_container_width=True,
                     column_config={
                         "Ø Verspätung (s)": st.column_config.NumberColumn(format="%.1f s"),
                         "OTP (%)": st.column_config.NumberColumn(format="%.1f %%"),
                         "Puffer (s)": st.column_config.NumberColumn(format="%d s"),
                     })
        rec_a = recommendation_text(line_a, stats_a, worst_a)
        box(rec_a, kind=recommendation_box_color(stats_a["otp_pct"]))

    with col_wb:
        st.caption(f"Linie {line_b}")
        st.dataframe(worst_b, hide_index=True, use_container_width=True,
                     column_config={
                         "Ø Verspätung (s)": st.column_config.NumberColumn(format="%.1f s"),
                         "OTP (%)": st.column_config.NumberColumn(format="%.1f %%"),
                         "Puffer (s)": st.column_config.NumberColumn(format="%d s"),
                     })
        rec_b = recommendation_text(line_b, stats_b, worst_b)
        box(rec_b, kind=recommendation_box_color(stats_b["otp_pct"]))


# ══════════════════════════════════════════════════════════════════════════════
# SEITE 3 — DELAY VORHERSAGEN
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Verspätung vorhersagen":
    st.markdown('<div class="page-title">Verspätung vorhersagen</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">'
        'Was kostet ein Schneetag auf Linie 11 um 21 Uhr? '
        'Zwei Szenarien direkt vergleichen — das Modell rechnet live.'
        '</div>',
        unsafe_allow_html=True,
    )

    box(
        "<strong>Modell: LightGBM v1</strong> · MAE 45,7s · trainiert auf 41,2 Mio. Fahrten 2023–2024 · "
        "32 Features die zum Planungszeitpunkt bekannt sind (kein prev_trip_delay). "
        "Das ist der echte Pre-Trip-Use-Case: Delay vor Fahrtbeginn abschätzen.",
        kind="insight",
    )

    st.markdown("---")

    # ── Zwei Szenario-Spalten ──
    col_s1, col_s2 = st.columns(2, gap="large")

    _DEFAULTS_A = {"hour": 8,  "weekday": 0, "month": 2, "snow": False, "temp": 5,  "stop": "Glattpark"}
    _DEFAULTS_B = {"hour": 21, "weekday": 3, "month": 2, "snow": True,  "temp": -2, "stop": "Glattpark"}

    def scenario_form(col, key_prefix: str, label: str, defaults: dict):
        with col:
            st.markdown(f"**{label}**")

            s_line = st.selectbox(
                "Linie", ALL_LINES,
                index=ALL_LINES.index("11") if "11" in ALL_LINES else 0,
                format_func=lambda x: f"Linie {x}",
                key=f"{key_prefix}_line",
            )
            line_stops = sorted(
                lookup_df
                .filter(pl.col("line_name").cast(pl.String) == str(s_line))
                .select("stop_name")
                .to_series()
                .unique()
                .to_list()
            )
            default_stop_idx = line_stops.index(defaults["stop"]) if defaults["stop"] in line_stops else 0
            s_stop = st.selectbox(
                "Haltestelle", line_stops,
                index=default_stop_idx,
                key=f"{key_prefix}_stop",
            )

            c1, c2 = st.columns(2)
            s_hour    = c1.selectbox("Stunde", list(range(24)), index=defaults["hour"],
                                     format_func=lambda h: f"{h:02d}:00",
                                     key=f"{key_prefix}_hour")
            s_weekday = c2.selectbox("Wochentag", list(range(7)), index=defaults["weekday"],
                                     format_func=lambda d: WEEKDAY_LABELS[d],
                                     key=f"{key_prefix}_weekday")
            s_month = st.selectbox(
                "Monat", list(range(1, 13)), index=defaults["month"] - 1,
                format_func=lambda m: [
                    "Jan","Feb","Mär","Apr","Mai","Jun",
                    "Jul","Aug","Sep","Okt","Nov","Dez"
                ][m-1],
                key=f"{key_prefix}_month",
            )
            st.markdown("**Wetter & Kontext**")
            w1, w2 = st.columns(2)
            s_snow    = w1.checkbox("Schnee",             value=defaults["snow"], key=f"{key_prefix}_snow")
            s_rain    = w2.checkbox("Regen",              key=f"{key_prefix}_rain")
            s_event   = w1.checkbox("Grossveranstaltung", key=f"{key_prefix}_event")
            s_holiday = w2.checkbox("Feiertag",           key=f"{key_prefix}_holiday")
            s_temp    = st.slider("Temperatur (°C)", -10, 40, defaults["temp"],
                                  key=f"{key_prefix}_temp")

            return {
                "line": s_line, "stop": s_stop, "hour": s_hour,
                "weekday": s_weekday, "month": s_month,
                "snow": s_snow, "rain": s_rain,
                "event": s_event, "holiday": s_holiday, "temp": s_temp,
            }

    sc1 = scenario_form(col_s1, "s1", "Szenario A", _DEFAULTS_A)
    sc2 = scenario_form(col_s2, "s2", "Szenario B", _DEFAULTS_B)

    st.markdown("---")
    st.button("Aktualisieren ▶", type="primary", use_container_width=True)

    if True:
        model, meta = load_model()

        def predict(sc: dict) -> float:
            fdf = build_feature_row(
                sc["line"], sc["stop"], sc["hour"], sc["weekday"], sc["month"],
                sc["temp"], sc["rain"], sc["snow"], sc["holiday"], sc["event"],
            )
            fdf = fdf[meta["features"]]
            return float(model.predict(fdf, num_iteration=meta["best_iteration"])[0])

        pred1 = predict(sc1)
        pred2 = predict(sc2)
        diff  = pred2 - pred1

        def result_block(col, pred: float, sc: dict, label: str):
            with col:
                css = "pred-green" if pred < 30 else "pred-amber" if pred < 90 else "pred-red"
                lbl = "pünktlich" if pred < 30 else "leichte Verspätung" if pred < 60 else "erhöhte Verspätung" if pred < 90 else "erhebliche Verspätung"
                st.markdown(f"""
                <div class="pred-box {css}">
                    <div class="pred-val">{pred:+.0f}s</div>
                    <div class="pred-lbl">{label} — {lbl}</div>
                </div>""", unsafe_allow_html=True)
                st.caption(
                    f"Linie {sc['line']} · {sc['stop'].replace('Zürich, ', '')} · "
                    f"{sc['hour']:02d}:00 · {WEEKDAY_LABELS[sc['weekday']]} · "
                    + (", ".join(filter(None, [
                        "Schnee" if sc["snow"] else "",
                        "Regen" if sc["rain"] else "",
                        "Event" if sc["event"] else "",
                    ])) or "Normalbetrieb")
                )

        res1, res2 = st.columns(2, gap="large")
        result_block(res1, pred1, sc1, "Szenario A")
        result_block(res2, pred2, sc2, "Szenario B")

        # ── Differenz-Box ──
        st.markdown("---")
        if abs(diff) < 5:
            box("Kein wesentlicher Unterschied zwischen den Szenarien (< 5s).", kind="insight")
        elif diff > 0:
            box(
                f"<strong>Szenario B kostet {diff:+.0f}s mehr Verspätung</strong> als Szenario A. "
                + (f"Davon entfallen schätzungsweise +54s auf Schnee." if sc2["snow"] and not sc1["snow"] else "")
                + (f" Events treiben die Verspätung abends signifikant." if sc2["event"] and not sc1["event"] else ""),
                kind="warn",
            )
        else:
            box(
                f"<strong>Szenario B liegt {abs(diff):.0f}s unter Szenario A.</strong> "
                "Günstigere Bedingungen wirken sich direkt aus.",
                kind="rec",
            )

        # ── Vergleichs-Chart ──
        fig_bar = go.Figure(go.Bar(
            x=["Szenario A", "Szenario B"],
            y=[pred1, pred2],
            marker_color=[AMBER if pred1 >= 30 else GREEN, RED if pred2 >= 90 else AMBER if pred2 >= 30 else GREEN],
            text=[f"{pred1:+.0f}s", f"{pred2:+.0f}s"],
            textposition="outside",
            width=0.4,
        ))
        fig_bar.add_hline(y=0, line_color="#ccc", line_width=1)
        fig_bar.update_layout(
            height=280,
            margin=dict(t=20, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(gridcolor="#eee", title="Vorhergesagte Verspätung (s)"),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.markdown("""
        <div style="color:#a0aec0;text-align:center;padding:2rem 0;font-size:0.95rem">
            Szenarien konfigurieren → <strong>Berechnen</strong> klicken<br>
            <span style="font-size:0.85rem">
            Tipp: Vergleiche Normal vs. Schnee, oder Morgenrush vs. 21 Uhr
            </span>
        </div>
        """, unsafe_allow_html=True)
