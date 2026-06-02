"""
Zürich Tram Flow — Interaktives Dashboard
Streamlit + Plotly · Deutsch · Vier Seiten: Überblick · Analyse · Vorhersage · Empfehlungen
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

# ─── Pfade ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent.parent
AGG  = Path(__file__).resolve().parent / "data"
MODELS = ROOT / "data" / "models"
PUBLIC = ROOT / "public"
IMG    = PUBLIC / "img"

# ─── Seiten-Konfiguration ────────────────────────────────────────────────────

st.set_page_config(
    page_title="Zürich Tram Flow",
    page_icon="🚋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Design-Token ────────────────────────────────────────────────────────────

NAVY   = "#1a3a5c"
BLUE   = "#2E86AB"
GREEN  = "#27ae60"
AMBER  = "#e67e22"
RED    = "#e74c3c"
MUTED  = "#718096"

LINE_COLORS = {
    "2": "#E20A16", "3": "#00892F", "4": "#11296F", "6": "#CA7D3C",
    "7": "#000000", "8": "#8AB51F", "9": "#11296F", "10": "#E12472",
    "11": "#00892F", "12": "#92D6E3", "13": "#FFCC00", "14": "#008DC5",
    "15": "#E20A16", "17": "#8E224D",
}

WEEKDAY_LABELS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTH_TO_SEASON = {12:1,1:1,2:1, 3:2,4:2,5:2, 6:3,7:3,8:3, 9:4,10:4,11:4}
MONTH_LABELS = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

st.markdown("""
<style>
/* Basis */
section[data-testid="stSidebar"] { background: #1a3a5c; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] .stRadio label { font-size: 1.05rem; padding: 0.4rem 0; }

/* Hero */
.hero-box {
    background: linear-gradient(135deg, #1a3a5c 0%, #2E86AB 100%);
    color: white; padding: 2rem 2.5rem 1.5rem; border-radius: 10px;
    margin-bottom: 1.5rem;
}
.hero-box h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
.hero-box p  { font-size: 1.05rem; opacity: 0.85; max-width: 680px; }

/* KPI Kacheln */
.kpi-row { display: flex; gap: 1rem; margin: 1.2rem 0; flex-wrap: wrap; }
.kpi { background: white; border-left: 4px solid #2E86AB; padding: 0.9rem 1.3rem;
       border-radius: 6px; min-width: 130px; box-shadow: 0 1px 4px rgba(0,0,0,.07); }
.kpi .val { font-size: 1.8rem; font-weight: 700; color: #1a3a5c; }
.kpi .lbl { font-size: 0.78rem; color: #718096; text-transform: uppercase;
            letter-spacing: 0.05em; }

/* Abschnitt-Header */
.sec-header {
    font-size: 1.15rem; font-weight: 700; color: #1a3a5c;
    border-bottom: 2px solid #2E86AB; padding-bottom: 0.3rem;
    margin: 2rem 0 0.8rem;
}
.finding-label {
    display: inline-block; background: #e8f4fb; color: #2E86AB;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
    padding: 0.2rem 0.6rem; border-radius: 3px; margin-bottom: 0.4rem;
    text-transform: uppercase;
}
.finding-title { font-size: 1.25rem; font-weight: 700; color: #1a3a5c; margin-bottom: 0.5rem; }
.finding-body  { color: #4a5568; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem; }

/* Prediction */
.pred-box { padding: 1.5rem 2rem; border-radius: 8px; margin: 1rem 0; }
.pred-green { background: #f0fff4; border-left: 5px solid #27ae60; }
.pred-amber { background: #fffbeb; border-left: 5px solid #e67e22; }
.pred-red   { background: #fff5f5; border-left: 5px solid #e74c3c; }
.pred-val   { font-size: 3rem; font-weight: 800; }
.pred-green .pred-val { color: #27ae60; }
.pred-amber .pred-val { color: #e67e22; }
.pred-red   .pred-val { color: #e74c3c; }
.pred-lbl   { font-size: 0.9rem; color: #718096; margin-top: 0.25rem; }

/* Projekt-Intro */
.intro-box {
    background: #f8fafc; border-left: 4px solid #2E86AB;
    padding: 1rem 1.4rem; border-radius: 6px; font-size: 0.9rem;
    color: #4a5568; margin-bottom: 1.5rem; line-height: 1.65;
}
</style>
""", unsafe_allow_html=True)

# ─── Daten laden (gecached) ──────────────────────────────────────────────────

@st.cache_data(show_spinner="Daten laden …")
def load_agg():
    stop      = pl.read_parquet(AGG / "stop_agg.parquet")
    hourly    = pl.read_parquet(AGG / "hourly_agg.parquet")
    weather   = pl.read_parquet(AGG / "weather_agg.parquet")
    line      = pl.read_parquet(AGG / "line_agg.parquet")
    lookup    = pl.read_parquet(AGG / "stop_line_lookup.parquet")
    route     = pl.read_parquet(AGG / "route_profile.parquet")
    return stop, hourly, weather, line, lookup, route

@st.cache_resource(show_spinner="Modell laden …")
def load_model():
    m = lgb.Booster(model_file=str(MODELS / "lgbm_v1.txt"))
    with open(MODELS / "lgbm_v1_meta.json") as f:
        meta = json.load(f)
    return m, meta

# ─── Chart-Hilfsfunktionen ───────────────────────────────────────────────────

def chart_stop_map(stop_df: pl.DataFrame) -> go.Figure:
    df = stop_df.to_pandas()
    df["delay_label"] = df["mean_delay"].round(1).astype(str) + "s"
    df["otp_label"]   = df["otp_pct"].round(1).astype(str) + "%"

    fig = px.scatter_mapbox(
        df, lat="lat", lon="lon",
        color="mean_delay",
        size="mean_delay",
        size_max=22,
        hover_name="stop_name",
        hover_data={"lat": False, "lon": False,
                    "mean_delay": ":.1f", "otp_label": True, "district_nr": True},
        color_continuous_scale=[[0, "#27ae60"], [0.4, "#f39c12"], [1, "#e74c3c"]],
        range_color=[df["mean_delay"].min(), df["mean_delay"].quantile(0.95)],
        zoom=11.5, center={"lat": 47.377, "lon": 8.543},
        mapbox_style="carto-positron",
        labels={"mean_delay": "Ø Verspätung (s)", "otp_label": "OTP"},
        height=520,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      coloraxis_colorbar=dict(title="Ø Delay (s)", thickness=12))
    return fig


def chart_heatmap(hourly_df: pl.DataFrame) -> go.Figure:
    df = hourly_df.to_pandas()
    pivot = df.pivot(index="hour", columns="weekday", values="mean_delay")
    pivot.columns = [WEEKDAY_LABELS[c] for c in pivot.columns]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#27ae60"], [0.4, "#f39c12"], [1, "#e74c3c"]],
        hoverongaps=False,
        colorbar=dict(title="Ø Delay (s)", thickness=12),
        hovertemplate="<b>%{y}:00 Uhr · %{x}</b><br>Ø Delay: %{z:.1f}s<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Wochentag", yaxis_title="Stunde",
        yaxis=dict(autorange="reversed"),
        height=380, margin=dict(t=10, b=40),
    )
    return fig


def chart_weather(weather_df: pl.DataFrame) -> go.Figure:
    df = weather_df.sort("mean_delay").to_pandas()
    colors = [GREEN if v < 30 else AMBER if v < 60 else RED for v in df["mean_delay"]]
    fig = go.Figure(go.Bar(
        x=df["mean_delay"].round(1),
        y=df["weather_type"],
        orientation="h",
        marker_color=colors,
        text=df["mean_delay"].round(1).astype(str) + "s",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Ø Delay: %{x:.1f}s<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Ø Verspätung (s)", yaxis_title="",
        height=280, margin=dict(t=10, b=40, l=10),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(gridcolor="#eee"),
    )
    return fig


def chart_line_bar(line_df: pl.DataFrame) -> go.Figure:
    df = line_df.sort("mean_delay", descending=True).to_pandas()
    df["line_name"] = df["line_name"].astype(str)
    colors = [LINE_COLORS.get(ln, "#8c8c8c") for ln in df["line_name"]]
    fig = go.Figure(go.Bar(
        x=df["line_name"],
        y=df["mean_delay"].round(1),
        marker_color=colors,
        marker_line_color="rgba(0,0,0,0.1)",
        marker_line_width=1,
        text=df["mean_delay"].round(0).astype(int).astype(str) + "s",
        textposition="outside",
        hovertemplate="<b>Linie %{x}</b><br>Ø Delay: %{y:.1f}s<br>OTP: %{customdata:.1f}%<extra></extra>",
        customdata=df["otp_pct"].round(1),
    ))
    netz_avg = float(line_df["mean_delay"].mean())
    fig.add_hline(y=netz_avg, line_dash="dash", line_color=MUTED,
                  annotation_text=f"Netz Ø {netz_avg:.1f}s", annotation_position="top right")
    fig.update_layout(
        xaxis_title="Linie", yaxis_title="Ø Verspätung (s)",
        height=350, margin=dict(t=30, b=40),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(gridcolor="#eee"),
    )
    return fig


def chart_cascade(route_df: pl.DataFrame, line: str = "11") -> go.Figure:
    df = (
        route_df.filter(pl.col("line_name") == line)
        .sort("mean_delay")
        .to_pandas()
        .reset_index(drop=True)
    )
    df["stop_idx"] = range(len(df))
    color = LINE_COLORS.get(str(line), BLUE)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["stop_idx"], y=df["mean_delay"],
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=6, color=color),
        hovertemplate="<b>%{customdata}</b><br>Ø Delay: %{y:.1f}s<extra></extra>",
        customdata=df["stop_name"],
        name=f"Linie {line}",
    ))
    fig.update_layout(
        xaxis_title="Haltestellen (nach mittlerem Delay sortiert)",
        yaxis_title="Ø Verspätung (s)",
        height=320, margin=dict(t=20, b=40),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(gridcolor="#eee"), showlegend=False,
    )
    return fig

# ─── Prediction ──────────────────────────────────────────────────────────────

def build_feature_row(line_name, stop_name, hour, weekday, month,
                      temperature, has_rain, has_snow, is_holiday, has_event,
                      lookup_df: pl.DataFrame) -> pd.DataFrame:
    row_data = lookup_df.filter(
        (pl.col("stop_name") == stop_name) & (pl.col("line_name") == line_name)
    )
    if len(row_data) == 0:
        district_nr, n_lines_at_stop, dwell_time, n_stops_line = 1, 1, 0, 20
        is_start_stop = is_end_stop = False
    else:
        r = row_data.row(0, named=True)
        district_nr      = r["district_nr"]
        n_lines_at_stop  = r["n_lines_at_stop"]
        dwell_time       = int(r["dwell_time_median"] or 0)
        n_stops_line     = r["n_stops_line"]
        is_start_stop    = r["is_start_stop"]
        is_end_stop      = r["is_end_stop"]

    season              = MONTH_TO_SEASON[month]
    is_weekend          = weekday >= 5
    is_november         = month == 11
    has_heavy_rain      = False
    is_hot              = temperature >= 30
    event_weight        = 3 if has_event else 0
    event_weight_x_hour = event_weight * hour
    is_late_night_weekend = is_weekend and (hour >= 22 or hour <= 4)

    row = {
        "line_name": line_name, "stop_name": stop_name,
        "district_nr": district_nr, "temperature": float(temperature),
        "precipitation": 2.0 if has_rain else 0.0, "wind_speed": 5.0,
        "flood_intensity": 0, "event_type": "Konzert" if has_event else "no_event",
        "event_size": 3 if has_event else 0, "hour": hour, "weekday": weekday,
        "month": month, "year": 2025, "season": season, "is_weekend": is_weekend,
        "is_november": is_november, "gtfs_year": "j24_j25", "has_rain": has_rain,
        "has_heavy_rain": has_heavy_rain, "has_snow": has_snow, "has_flood": False,
        "is_hot": is_hot, "is_holiday": is_holiday, "has_event": has_event,
        "event_weight": event_weight, "dwell_time": dwell_time,
        "n_lines_at_stop": n_lines_at_stop, "n_stops_line": n_stops_line,
        "is_start_stop": is_start_stop, "is_end_stop": is_end_stop,
        "event_weight_x_hour": event_weight_x_hour,
        "is_late_night_weekend": is_late_night_weekend,
    }
    df = pd.DataFrame([row])
    for col in ["line_name", "stop_name", "event_type", "season", "gtfs_year"]:
        df[col] = df[col].astype("category")
    return df


# ─── Seite 0 — Überblick ─────────────────────────────────────────────────────

def page_ueberblick(stop_df, line_df):
    st.markdown("""
    <div class="hero-box">
        <h1>🚋 Zürich Tram Flow</h1>
        <p>Die Verspätungen im Zürcher Tramnetz sind kein Zufallsprodukt — sie sind
        im Fahrplandesign verankert. Dieses Dashboard zeigt wo, wann und warum
        Verspätungen entstehen, und macht sie live vorhersagbar.</p>
    </div>
    """, unsafe_allow_html=True)

    netz_delay = float(stop_df["mean_delay"].mean())
    netz_otp   = float(stop_df["otp_pct"].mean())
    worst_stop = stop_df.sort("mean_delay", descending=True).row(0, named=True)

    kpis = [
        ("94,4 Mio.", "Datenpunkte", "2023–2025 · VBZ Zürich"),
        (f"{netz_otp:.1f}%", "Pünktlichkeit (OTP)", "Ziel: 95% · Lücke: −8pp"),
        ("18,56s", "Modell MAE", "LightGBM v2 · 63% unter Baseline"),
        ("63", "Analyse-Findings", "aus 12 Notebooks"),
    ]
    cols = st.columns(4)
    for col, (val, lbl, sub) in zip(cols, kpis):
        col.markdown(f"""
        <div class="kpi">
            <div class="val">{val}</div>
            <div class="lbl">{lbl}</div>
            <div style="font-size:0.73rem;color:#a0aec0;margin-top:2px">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="intro-box">
        <strong>Was ist das?</strong> — Eine vollständige Analyse des Zürcher Tramnetzes
        (VBZ) auf Basis von 94,4 Millionen Halt-Ereignissen über drei Jahre.
        Ziel: Verstehen warum 13% aller Fahrten zu spät kommen — und diese Muster
        mit Machine Learning vorhersagen.<br><br>
        <strong>Was hier passiert:</strong> Analyse → Befund → Modell → Empfehlung.
        Die Verspätungen sind strukturell (nicht zufällig), sie konzentrieren sich
        an der Peripherie, kaskadieren entlang der Strecke, und reagieren stark auf
        Schnee. Das Modell bestätigt jeden dieser Befunde quantitativ.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sec-header'>Netzwerk auf einen Blick</div>",
                unsafe_allow_html=True)
    st.caption("Ø Ankunftsverspätung pro Haltestelle · Testjahr 2025 · Hover für Details")
    st.plotly_chart(chart_stop_map(stop_df), use_container_width=True)

    st.markdown("<div class='sec-header'>Verspätung nach Linie</div>",
                unsafe_allow_html=True)
    st.caption("Alle 16 Tramlinien · Punkte über der gestrichelten Linie liegen über Netzschnitt")
    st.plotly_chart(chart_line_bar(line_df), use_container_width=True)

    st.markdown("---")
    st.markdown(f"""
    **Schlimmste Haltestelle:** {worst_stop['stop_name']} — {worst_stop['mean_delay']:.1f}s Ø Delay
    · OTP {worst_stop['otp_pct']:.1f}%
    · Netzschnitt: {netz_delay:.1f}s
    """)


# ─── Seite 1 — Analyse & Findings ────────────────────────────────────────────

def page_analyse(stop_df, hourly_df, weather_df, line_df, route_df):
    st.title("Analyse & Findings")
    st.markdown("""
    <div class="intro-box">
        Drei zentrale Befunde aus 63 Analyse-Findings — jeweils mit interaktivem
        Chart als Beweis. Alle Daten stammen aus dem Testjahr 2025
        (~29 Mio. Halt-Ereignisse).
    </div>
    """, unsafe_allow_html=True)

    # ── Finding 1: Peripherie ──
    st.markdown("<div class='finding-label'>Finding F-GEO-01</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='finding-title'>Die Peripherie leidet — nicht das Zentrum</div>",
                unsafe_allow_html=True)
    st.markdown("""<div class='finding-body'>
        Friedhof Enzenbühl (Kreis 7) hat 93,8s mittleren Delay — Paradeplatz
        (Knotenpunkt von 14 Linien) nur 14s. Das widerlegt die Intuition:
        Überlastung im Zentrum ist nicht das Problem. Fehlender Fahrplanpuffer
        an den Aussenkorridoren ist es.
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(chart_stop_map(stop_df), use_container_width=True)

    st.divider()

    # ── Finding 2: Temporal ──
    st.markdown("<div class='finding-label'>Finding F-TMP-03</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='finding-title'>21 Uhr schlägt den Morgenrush — Events treiben den Nachtpeak</div>",
                unsafe_allow_html=True)
    st.markdown("""<div class='finding-body'>
        Der höchste Delay-Peak liegt nicht um 8h, sondern um 21h — getrieben
        durch Grossveranstaltungen (Konzerte, Super League). Spätnacht-Wochenende
        ist überraschend hoch: 71,3% aller Haltestellen haben 0s dwell_time —
        kein eingebauter Puffer für Erholung.
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(chart_heatmap(hourly_df), use_container_width=True)

    st.divider()

    # ── Finding 3: Meteo ──
    st.markdown("<div class='finding-label'>Finding F-MET-02</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='finding-title'>Schnee kostet 54 Sekunden — Regen ist Rauschen</div>",
                unsafe_allow_html=True)
    st.markdown("""<div class='finding-body'>
        Schnee erhöht den mittleren Delay um ~54s und senkt die OTP um
        −10,9 Prozentpunkte. Regen dagegen zeigt kaum Effekt. Der Unterschied
        ist geografisch trennbar: Schnee trifft Höhenlagen (Linie 10, 4, 12),
        Regen die Flusstäler (Linie 5).
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(chart_weather(weather_df), use_container_width=True)

    st.divider()

    # ── Finding 4: Kaskade ──
    st.markdown("<div class='finding-label'>Finding F-NET-07</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='finding-title'>Delay kaskadiert — Pearson r ≥ 0,85 netzweit</div>",
                unsafe_allow_html=True)
    st.markdown("""<div class='finding-body'>
        Alle 16 Tramlinien zeigen eine Korrelation von r ≥ 0,85 zwischen
        aufeinanderfolgenden Halten. Ein verspätetes Tram macht das nächste
        Tram verspätet. Das bestätigt das Modell: <code>prev_trip_delay</code>
        als Feature halbiert den Fehler — MAE von 45,7s auf 18,56s.
    </div>""", unsafe_allow_html=True)

    available_lines = sorted(route_df["line_name"].unique().to_list())
    sel_line = st.selectbox(
        "Linie anzeigen",
        available_lines,
        index=available_lines.index("11") if "11" in available_lines else 0,
        key="cascade_line",
    )
    st.plotly_chart(chart_cascade(route_df, sel_line), use_container_width=True)
    st.caption(
        "Haltestellen sortiert nach mittlerem Delay — zeigt wie Delay entlang der Route wächst."
    )


# ─── Seite 2 — Vorhersage ────────────────────────────────────────────────────

def page_vorhersage(lookup_df: pl.DataFrame):
    st.title("Delay-Vorhersage")
    st.markdown("""
    <div class="intro-box">
        <strong>Was ist das?</strong> — LightGBM v1 sagt die Ankunftsverspätung
        für eine konkrete Fahrt voraus. Das Modell kennt 32 Features die zum
        Planungszeitpunkt bekannt sind — kein <em>prev_trip_delay</em> nötig.
        Das ist der echte Pre-Trip-Use-Case: Fahrplaner oder Dispatcher kann
        Verspätungen vor Fahrtbeginn abschätzen.<br><br>
        <strong>Modell:</strong> LightGBM v1 · Trainiert auf 41,2 Mio. Fahrten
        (2023–2024) · Test-MAE 45,7s · MBE +8,3s
    </div>
    """, unsafe_allow_html=True)

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("**Fahrt konfigurieren**")

        all_lines = sorted(LINE_COLORS.keys())
        line = st.selectbox(
            "Linie",
            all_lines,
            index=all_lines.index("11") if "11" in all_lines else 0,
        )

        line_stops = sorted(
            lookup_df.filter(pl.col("line_name") == line)["stop_name"].cast(pl.String).unique().to_list()
        )
        if not line_stops:
            line_stops = sorted(lookup_df["stop_name"].cast(pl.String).unique().to_list())
        stop = st.selectbox("Haltestelle", line_stops)

        c1, c2 = st.columns(2)
        hour    = c1.selectbox("Stunde", list(range(24)), index=8,
                               format_func=lambda h: f"{h:02d}:00")
        weekday = c2.selectbox("Wochentag", list(range(7)),
                               format_func=lambda d: WEEKDAY_LABELS[d])

        month = st.selectbox(
            "Monat", list(range(1, 13)), index=0,
            format_func=lambda m: [
                "Januar","Februar","März","April","Mai","Juni",
                "Juli","August","September","Oktober","November","Dezember"
            ][m-1],
        )

        st.markdown("---")
        st.markdown("**Wetter & Kontext**")
        cw1, cw2 = st.columns(2)
        has_rain   = cw1.checkbox("Regen")
        has_snow   = cw2.checkbox("Schnee")
        is_holiday = cw1.checkbox("Feiertag")
        has_event  = cw2.checkbox("Grossveranstaltung")

        temperature = 15
        with st.expander("Temperatur (optional)"):
            temperature = st.slider("°C", -10, 40, 15)

        btn = st.button("Delay vorhersagen ▶", type="primary", use_container_width=True)

    with col_result:
        if btn:
            model, meta = load_model()
            fdf = build_feature_row(
                line, stop, hour, weekday, month, temperature,
                has_rain, has_snow, is_holiday, has_event, lookup_df
            )
            fdf = fdf[meta["features"]]
            pred = float(model.predict(fdf, num_iteration=meta["best_iteration"])[0])

            css = "pred-green" if pred < 30 else "pred-amber" if pred < 90 else "pred-red"
            lbl = (
                "pünktlich" if pred < 30
                else "leichte Verspätung" if pred < 90
                else "erhebliche Verspätung"
            )
            st.markdown(f"""
            <div class="pred-box {css}">
                <div class="pred-val">{pred:+.0f}s</div>
                <div class="pred-lbl">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Eingabe**")
            for k, v in [
                ("Linie / Haltestelle", f"{line} · {stop}"),
                ("Zeit", f"{hour:02d}:00 Uhr · {WEEKDAY_LABELS[weekday]}"),
                ("Monat / Saison", f"{MONTH_LABELS[month-1]} · Saison {MONTH_TO_SEASON[month]}"),
                ("Wetter", ", ".join(filter(None, [
                    "Regen" if has_rain else "",
                    "Schnee" if has_snow else "",
                    f"{temperature}°C",
                ]))),
                ("Kontext", ", ".join(filter(None, [
                    "Feiertag" if is_holiday else "",
                    "Grossveranstaltung" if has_event else "",
                ])) or "–"),
            ]:
                c1, c2 = st.columns([1, 2])
                c1.markdown(f"**{k}**")
                c2.markdown(v)

            with st.expander("Automatisch ermittelte Stop-Features"):
                row = lookup_df.filter(
                    (pl.col("stop_name") == stop) & (pl.col("line_name") == line)
                )
                if len(row) > 0:
                    r = row.row(0, named=True)
                    st.json({
                        "district_nr": r.get("district_nr"),
                        "n_lines_at_stop": r.get("n_lines_at_stop"),
                        "dwell_time_median_s": r.get("dwell_time_median"),
                        "is_start_stop": r.get("is_start_stop"),
                        "is_end_stop": r.get("is_end_stop"),
                        "n_stops_line": r.get("n_stops_line"),
                    })
        else:
            st.markdown("""
            <div style="color:#a0aec0;text-align:center;margin-top:4rem;">
                ← Fahrt konfigurieren<br>dann <strong>„Delay vorhersagen"</strong> klicken
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **Modellvergleich**

            | Modell | Test MAE | MBE |
            |:-------|:--------:|:---:|
            | Stop-Mittelwert (Baseline) | 50,0s | +10,1s |
            | LightGBM v1 (Pre-Trip) | 45,7s | +8,3s |
            | LightGBM v2 (+ Kaskadenindikator) | **18,56s** | −0,69s |

            v2 nutzt `prev_trip_delay` — nicht zum Planungszeitpunkt verfügbar.
            v1 ist der echte Pre-Trip-Use-Case.
            """)


# ─── Seite 3 — Empfehlungen ──────────────────────────────────────────────────

def page_empfehlungen():
    st.title("Empfehlungen & Scheduling")
    st.markdown("""
    <div class="intro-box">
        <strong>Vorhersagbar heisst steuerbar.</strong> — Ein MAE von 18,56s
        ist nur möglich wenn Delays Muster folgen. Zufällige Ereignisse
        lassen sich nicht so gut vorhersagen. Das Modell identifiziert
        welche Stops, Linien und Betriebssituationen planmäßigen Puffer
        benötigen — und macht damit Analyse-Findings direkt zu
        Fahrplan-Empfehlungen.
    </div>
    """, unsafe_allow_html=True)

    sched_map = PUBLIC / "img" / "scheduling-recommendations-map.html"
    if sched_map.exists():
        st.markdown("**Risiko-Karte: Welche Stops brauchen Puffer — und wann?**")
        st.components.v1.html(
            sched_map.read_text(encoding="utf-8"), height=560, scrolling=True
        )
    else:
        st.info(
            "Scheduling-Karte noch nicht exportiert. "
            "Notebook `06_prediction_7-scheduling_recommendations.ipynb` ausführen."
        )

    st.markdown("**4 Handlungsfelder**")
    handlungsfelder = [
        ("🗺 Geo-basiertes Puffer-Design",
         "Stops mit strukturellem Delay > 60s (z.B. Friedhof Enzenbühl, Balgrist) "
         "brauchen 30–45s zusätzlichen Fahrplanpuffer. Aktuell haben 71,3% aller "
         "Stops 0s dwell_time."),
        ("❄️ Wetter-adaptiver Betrieb",
         "Schnee-Ereignisse erfordern ein separates Fahrplanprofil mit +20–30s "
         "Puffer auf exponierten Linien (L10, L4, L12). Regen-Tage erfordern "
         "keinen nennenswerten Eingriff."),
        ("🎭 Event-Kapazitätsplanung",
         "21h-Peaks entstehen durch Grossveranstaltungen. Nachfragebasierte "
         "Taktanpassung nach Konzert-/Sportevents würde den Nacht-Peak reduzieren."),
        ("🔗 Kaskaden-Prävention",
         "Linie 11 zeigt die stärkste Kaskade (r=0,91). Planmäßige "
         "Erholungspunkte (Wendezeiten an Endstationen) würden den "
         "Kaskadeneffekt unterbrechen."),
    ]
    for titel, text in handlungsfelder:
        with st.expander(titel, expanded=True):
            st.markdown(text)

    st.markdown("---")
    st.markdown("**Weiterführendes**")
    c1, c2, c3 = st.columns(3)
    c1.markdown("📄 [Vollständiger Report](../public/report.html)")
    c2.markdown("📊 [Presentation](../public/presentation.html)")
    c3.markdown("💻 [GitHub Repository](https://github.com/kaywiegand/zh-tram-flow)")


# ─── Sidebar + Routing ───────────────────────────────────────────────────────

def main():
    stop_df, hourly_df, weather_df, line_df, lookup_df, route_df = load_agg()

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:1rem 0 0.5rem">
            <div style="font-size:1.4rem;font-weight:700">🚋 Zürich Tram Flow</div>
            <div style="font-size:0.8rem;opacity:0.7;margin-top:0.3rem">
                Verspätungsanalyse · 2023–2025 · VBZ
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["🏠 Überblick", "🔍 Analyse & Findings", "🎯 Vorhersage", "📋 Empfehlungen"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.78rem;opacity:0.6'>"
            "Modell: LightGBM v1<br>"
            "MAE: 45,7s (Test 2025)<br>"
            "Datenpunkte: 94,4 Mio.<br>"
            "Findings: 63"
            "</div>",
            unsafe_allow_html=True,
        )

    if page == "🏠 Überblick":
        page_ueberblick(stop_df, line_df)
    elif page == "🔍 Analyse & Findings":
        page_analyse(stop_df, hourly_df, weather_df, line_df, route_df)
    elif page == "🎯 Vorhersage":
        page_vorhersage(lookup_df)
    else:
        page_empfehlungen()


if __name__ == "__main__" or True:
    main()
