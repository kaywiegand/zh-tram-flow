"""
Zurich Tram Flow — Explorer Dashboard v2
Drei interaktive Tools für Stakeholder nach der Präsentation.
Starten: uv run streamlit run apps/dashboard/app_v2.py
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
.block-container { padding-top: 1.5rem; max-width: 1200px; }

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
    lookup = pl.read_parquet(AGG / "stop_line_lookup.parquet")
    return stop, line, route, lookup

@st.cache_resource(show_spinner=False)
def load_model():
    m = lgb.Booster(model_file=str(MODELS / "lgbm_v1.txt"))
    with open(MODELS / "lgbm_v1_meta.json") as f:
        meta = json.load(f)
    return m, meta

stop_df, line_df, route_df, lookup_df = load_data()

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

def plot_line_map_with_geometry(line: str, route: pd.DataFrame) -> go.Figure:
    """Karte mit echtem Linienzug (GTFS Shape) + gefilterten Haltestellen.

    Logik:
    1. GTFS Shapes laden (echte Gleisgeometrie mit hunderten Zwischenpunkten)
    2. Route stops filtern: nur ≥5% der Hauptroute-Frequenz (entfernt Varianten)
    3. Bubble-Größe power-skaliert (2-24px, nicht linear)
    4. Zwei Layer: Linienzug (Tramfarbe) + Blasen (Delay-Farbcodierung)
    """
    # Layer 1: GTFS Shape (echte Gleisgeometrie)
    shapes = load_gtfs_shapes(line)

    # Layer 2: Filter route to main stops (consistent with bar chart)
    if len(route) > 0:
        route_copy = filter_route_for_display(route)

        # Bubble-Größe: power-scaled (nicht linear)
        if len(route_copy) > 0 and "mean_delay" in route_copy.columns:
            delays = route_copy["mean_delay"].values
            d_min, d_max = float(np.nanmin(delays)), float(np.nanmax(delays))
            norm = (delays - d_min) / (d_max - d_min + 1e-9)
            route_copy["bubble"] = 2 + (norm ** 1.7) * 22  # power-scaled, 2-24px
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
                colorbar=dict(title="Delay (s)", thickness=12),
            ),
            text=[
                f"<b>{stop}</b><br>Ø Delay: {delay:.1f}s<br>OTP: {otp:.1f}%"
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

def route_for_line(line: str) -> pd.DataFrame:
    """Route-Profil einer Linie — geografisch sortiert mit OTP + dwell_time.

    NOTE: route_df ist bereits nach lat/lon sortiert (geografische Reihenfolge entlang der Linie).
    Wir bereichern es nur mit stop_df-Metadaten, behalten aber die Sortierung.
    """
    r = (
        route_df
        .filter(pl.col("line_name").cast(pl.String) == str(line))
        .with_columns(pl.col("stop_name").cast(pl.Utf8))
        .join(
            stop_df.select(["stop_name", "otp_pct", "dwell_time_median"])
                .with_columns(pl.col("stop_name").cast(pl.Utf8)),
            on="stop_name", how="left",
        )
        # Keep geographic order (lat/lon) — don't re-sort
        .to_pandas()
    )
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
            "mean_delay": "Ø Delay (s)",
            "otp_pct": "OTP (%)",
            "dwell_time_median": "Puffer (s)",
        })
        .with_columns([
            pl.col("Ø Delay (s)").round(1),
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
            f"✅ <strong>Linie {line} liegt über Netzschnitt</strong> (OTP {otp:.1f}%). "
            f"Kein akuter Handlungsbedarf. Monitoring der {n_no_buf} Haltestellen ohne Puffer empfohlen."
        )
    elif otp >= 87:
        return (
            f"⚠️ <strong>Linie {line} — moderater Handlungsbedarf.</strong> "
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
        <div style="font-size:1.3rem;font-weight:800">Zurich Tram Flow</div>
        <div style="font-size:0.78rem;opacity:0.6;margin-top:0.3rem">
            Netz-Explorer · VBZ 2023–2025
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
    <div style="font-size:0.75rem;opacity:0.55;line-height:1.8">
        OTP netzweit: <strong>87,0%</strong><br>
        Ziel: 95% · Lücke −8 PP<br>
        16 Linien · 94,4 Mio. Datenpunkte
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SEITE 1 — LINIE ERKUNDEN
# ══════════════════════════════════════════════════════════════════════════════

if page == "Linie erkunden":
    st.markdown('<div class="page-title">Linie erkunden</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Wähle eine Linie — sieh wo der Delay entsteht '
        'und was dagegen getan werden kann.</div>',
        unsafe_allow_html=True,
    )

    sel_line = st.selectbox(
        "Linie wählen",
        ALL_LINES,
        index=ALL_LINES.index("11") if "11" in ALL_LINES else 0,
        format_func=lambda x: f"Linie {x}",
    )

    stats   = line_stats(sel_line)
    route   = route_for_line(sel_line)
    worst   = worst_stops_for_line(sel_line, n=5)

    if not stats:
        st.warning("Keine Daten für diese Linie.")
        st.stop()

    # ── KPIs ──
    otp   = stats["otp_pct"]
    delay = stats["mean_delay"]
    n_stops = stats["n_stops_line"]

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Pünktlichkeit (OTP)",
        f"{otp:.1f}%",
        delta=otp_delta_str(otp),
        delta_color="normal",
    )
    c2.metric("Ø Verspätung", f"{delay:.0f}s")
    c3.metric("Haltestellen", int(n_stops))

    st.markdown("---")

    # ── Delay-Profil: Plotly Bar (nach Delay sortiert) ──
    section_label("Delay pro Haltestelle")

    # Filter route to main stops (≥5% of frequency) — consistent with map
    route_filtered = filter_route_for_display(route)

    color = line_color(sel_line)
    bar_colors = [RED if d > 70 else AMBER if d > 40 else color for d in route_filtered["mean_delay"]]

    fig_route = go.Figure(go.Bar(
        x=route_filtered["stop_short"],
        y=route_filtered["mean_delay"].round(1),
        marker_color=bar_colors,
        marker_line_width=0,
        text=route["mean_delay"].round(0).astype(int).astype(str) + "s",
        textposition="outside",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Ø Delay: %{y:.1f}s<br>"
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
        xaxis=dict(tickangle=-40, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#eee", title="Ø Verspätung (s)"),
        showlegend=False,
    )
    st.plotly_chart(fig_route, use_container_width=True)

    # ── Karte: Echte Linienzug-Geometrie (GTFS) + gefilterte Blasen ──
    st.markdown("---")
    section_label("Karte — Linienzug mit Verspätungen")

    fig_map = plot_line_map_with_geometry(sel_line, route)
    st.plotly_chart(fig_map, use_container_width=True)

    # ── Top-5 Problemhaltestellen ──
    st.markdown("---")
    section_label("Top 5 Problemhaltestellen")

    col_tbl, col_rec = st.columns([3, 2], gap="large")

    with col_tbl:
        st.dataframe(
            worst,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Ø Delay (s)": st.column_config.NumberColumn(format="%.1f s"),
                "OTP (%)": st.column_config.NumberColumn(format="%.1f %%"),
                "Puffer (s)": st.column_config.NumberColumn(format="%d s"),
            },
        )

    with col_rec:
        rec_text = recommendation_text(sel_line, stats, worst)
        box(rec_text, kind=recommendation_box_color(stats["otp_pct"]))

    box(
        f"Tipp: Im Tab <strong>«Delay vorhersagen»</strong> kannst du für jede Haltestelle "
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

    stats_a = line_stats(line_a)
    stats_b = line_stats(line_b)
    route_a = route_for_line(line_a)
    route_b = route_for_line(line_b)
    worst_a = worst_stops_for_line(line_a, n=5)
    worst_b = worst_stops_for_line(line_b, n=5)

    st.markdown("---")

    # ── KPI-Vergleich ──
    section_label("Kennzahlen im Vergleich")

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
             stats_a.get("otp_pct", 0), stats_b.get("otp_pct", 0), suffix="%")
    kpi_pair(kpi_cols[1], "Ø Delay",
             stats_a.get("mean_delay", 0), stats_b.get("mean_delay", 0),
             fmt="{:.0f}", suffix="s", inverse=True)
    kpi_pair(kpi_cols[2], "P90 Delay",
             stats_a.get("p90_delay", 0), stats_b.get("p90_delay", 0),
             fmt="{:.0f}", suffix="s", inverse=True)
    kpi_pair(kpi_cols[3], "Haltestellen",
             stats_a.get("n_stops_line", 0), stats_b.get("n_stops_line", 0),
             fmt="{:.0f}", inverse=True)

    st.markdown("---")

    # ── Overlapping Bar Chart ──
    section_label("Delay-Verteilung — alle Haltestellen beider Linien")

    fig_cmp = go.Figure()
    for route, ln, opacity in [(route_a, line_a, 0.85), (route_b, line_b, 0.55)]:
        fig_cmp.add_trace(go.Bar(
            name=f"Linie {ln}",
            x=list(range(len(route))),
            y=route["mean_delay"].round(1),
            marker_color=line_color(ln),
            opacity=opacity,
            hovertemplate=(
                f"<b>Linie {ln}</b><br>%{{customdata}}<br>"
                "Ø Delay: %{y:.1f}s<extra></extra>"
            ),
            customdata=route["stop_short"],
        ))

    fig_cmp.add_hline(y=56, line_dash="dot", line_color="#aaa",
                      annotation_text="Netz-Ø 56s", annotation_position="top left")
    fig_cmp.update_layout(
        barmode="overlay",
        height=340,
        margin=dict(t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(title="Haltestellen (nach Delay sortiert)", showticklabels=False),
        yaxis=dict(gridcolor="#eee", title="Ø Verspätung (s)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    # ── Top-5 nebeneinander ──
    st.markdown("---")
    section_label("Top 5 Problemhaltestellen")

    col_wa, col_wb = st.columns(2, gap="large")
    with col_wa:
        st.caption(f"Linie {line_a}")
        st.dataframe(worst_a, hide_index=True, use_container_width=True,
                     column_config={
                         "Ø Delay (s)": st.column_config.NumberColumn(format="%.1f s"),
                         "OTP (%)": st.column_config.NumberColumn(format="%.1f %%"),
                         "Puffer (s)": st.column_config.NumberColumn(format="%d s"),
                     })
        rec_a = recommendation_text(line_a, stats_a, worst_a)
        box(rec_a, kind=recommendation_box_color(stats_a["otp_pct"]))

    with col_wb:
        st.caption(f"Linie {line_b}")
        st.dataframe(worst_b, hide_index=True, use_container_width=True,
                     column_config={
                         "Ø Delay (s)": st.column_config.NumberColumn(format="%.1f s"),
                         "OTP (%)": st.column_config.NumberColumn(format="%.1f %%"),
                         "Puffer (s)": st.column_config.NumberColumn(format="%d s"),
                     })
        rec_b = recommendation_text(line_b, stats_b, worst_b)
        box(rec_b, kind=recommendation_box_color(stats_b["otp_pct"]))


# ══════════════════════════════════════════════════════════════════════════════
# SEITE 3 — DELAY VORHERSAGEN
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Verspätung vorhersagen":
    st.markdown('<div class="page-title">Delay vorhersagen</div>', unsafe_allow_html=True)
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

    def scenario_form(col, key_prefix: str, label: str):
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
                ["stop_name"].cast(pl.String).unique().to_list()
            )
            s_stop = st.selectbox(
                "Haltestelle", line_stops,
                key=f"{key_prefix}_stop",
            )

            c1, c2 = st.columns(2)
            s_hour    = c1.selectbox("Stunde", list(range(24)), index=21,
                                     format_func=lambda h: f"{h:02d}:00",
                                     key=f"{key_prefix}_hour")
            s_weekday = c2.selectbox("Wochentag", list(range(7)), index=3,
                                     format_func=lambda d: WEEKDAY_LABELS[d],
                                     key=f"{key_prefix}_weekday")
            s_month = st.selectbox(
                "Monat", list(range(1, 13)), index=1,
                format_func=lambda m: [
                    "Jan","Feb","Mär","Apr","Mai","Jun",
                    "Jul","Aug","Sep","Okt","Nov","Dez"
                ][m-1],
                key=f"{key_prefix}_month",
            )
            st.markdown("**Wetter & Kontext**")
            w1, w2 = st.columns(2)
            s_snow    = w1.checkbox("Schnee",             key=f"{key_prefix}_snow")
            s_rain    = w2.checkbox("Regen",              key=f"{key_prefix}_rain")
            s_event   = w1.checkbox("Grossveranstaltung", key=f"{key_prefix}_event")
            s_holiday = w2.checkbox("Feiertag",           key=f"{key_prefix}_holiday")
            s_temp    = st.slider("Temperatur (°C)", -10, 40, 5 if s_snow else 15,
                                  key=f"{key_prefix}_temp")

            return {
                "line": s_line, "stop": s_stop, "hour": s_hour,
                "weekday": s_weekday, "month": s_month,
                "snow": s_snow, "rain": s_rain,
                "event": s_event, "holiday": s_holiday, "temp": s_temp,
            }

    sc1 = scenario_form(col_s1, "s1", "Szenario A")
    sc2 = scenario_form(col_s2, "s2", "Szenario B")

    st.markdown("---")
    run = st.button("Beide Szenarien berechnen ▶", type="primary", use_container_width=True)

    if run:
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
                lbl = "pünktlich" if pred < 30 else "leichte Verspätung" if pred < 90 else "erhebliche Verspätung"
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
                f"<strong>Szenario B kostet {diff:+.0f}s mehr Delay</strong> als Szenario A. "
                + (f"Davon entfallen schätzungsweise +54s auf Schnee." if sc2["snow"] and not sc1["snow"] else "")
                + (f" Events treiben den Delay abends signifikant." if sc2["event"] and not sc1["event"] else ""),
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
            yaxis=dict(gridcolor="#eee", title="Vorhergesagter Delay (s)"),
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
