"""
Zürich Tram Flow — Interactive Dashboard
Two modes: Explore (historical charts) + Predict (LightGBM v1 live inference)
"""

from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import pandas as pd
import polars as pl
import streamlit as st

# ─── Paths ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
MODELS = DATA / "models"
REPORTS = ROOT / "reports"
IMG = REPORTS / "img"

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Zürich Tram Flow",
    page_icon="🚋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ─────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .mode-header { font-size: 1.05rem; font-weight: 600; color: #888; margin-bottom: 0.5rem; }
    .prediction-box {
        background: #f0f4ff;
        border-left: 4px solid #1f4bd4;
        padding: 1.2rem 1.5rem;
        border-radius: 6px;
        margin-top: 1rem;
    }
    .prediction-value { font-size: 2.8rem; font-weight: 700; margin: 0; }
    .prediction-label { font-size: 0.9rem; color: #555; margin-top: 0.25rem; }
    .amber { color: #e67e00; }
    .red   { color: #cc1a1a; }
    .green { color: #1a8a1a; }
    .section-title {
        font-size: 1.2rem; font-weight: 700;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.3rem; margin-top: 1.5rem; margin-bottom: 0.8rem;
    }
    .chart-caption { font-size: 0.8rem; color: #777; margin-top: 0.2rem; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Data loading (cached) ────────────────────────────────────────────────────

@st.cache_data(show_spinner="Datenbasis laden …")
def load_lookup() -> tuple[dict, dict, list[str]]:
    """Build stop/line lookup tables from test_final.parquet (lazy scan)."""
    lf = pl.scan_parquet(DATA / "processed" / "test_final.parquet")

    stop_df = (
        lf.group_by("stop_name")
        .agg(
            pl.first("district_nr"),
            pl.first("n_lines_at_stop"),
            pl.median("dwell_time").alias("dwell_time_median"),
        )
        .collect()
    )
    stop_lookup: dict[str, dict] = {
        row["stop_name"]: {
            "district_nr": row["district_nr"],
            "n_lines_at_stop": row["n_lines_at_stop"],
            "dwell_time": int(row["dwell_time_median"] or 0),
        }
        for row in stop_df.iter_rows(named=True)
    }

    stop_line_df = (
        lf.group_by(["stop_name", "line_name"])
        .agg(
            pl.first("is_start_stop"),
            pl.first("is_end_stop"),
            pl.first("n_stops_line"),
        )
        .collect()
    )
    stop_line_lookup: dict[tuple, dict] = {
        (row["stop_name"], row["line_name"]): {
            "is_start_stop": row["is_start_stop"],
            "is_end_stop":   row["is_end_stop"],
            "n_stops_line":  row["n_stops_line"],
        }
        for row in stop_line_df.iter_rows(named=True)
    }

    lines_per_stop: dict[str, list[str]] = (
        lf.group_by("stop_name")
        .agg(pl.col("line_name").unique().sort().alias("lines"))
        .collect()
        .to_pandas()
        .set_index("stop_name")["lines"]
        .apply(list)
        .to_dict()
    )

    all_stops = sorted(stop_lookup.keys())
    return stop_lookup, stop_line_lookup, all_stops, lines_per_stop


@st.cache_resource(show_spinner="Modell laden …")
def load_model() -> tuple[lgb.Booster, dict]:
    model = lgb.Booster(model_file=str(MODELS / "lgbm_v1.txt"))
    with open(MODELS / "lgbm_v1_meta.json") as f:
        meta = json.load(f)
    return model, meta


# ─── Helpers ─────────────────────────────────────────────────────────────────

WEEKDAY_LABELS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTH_TO_SEASON = {12: 1, 1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3, 8: 3, 9: 4, 10: 4, 11: 4}

LINE_COLORS = {
    "2": "#E20A16", "3": "#00892F", "4": "#11296F", "6": "#CA7D3C",
    "7": "#000000", "8": "#8AB51F", "9": "#11296F", "10": "#E12472",
    "11": "#00892F", "12": "#92D6E3", "13": "#FFCC00", "14": "#008DC5",
    "15": "#E20A16", "17": "#8E224D",
}


def delay_color_class(delay_s: float) -> str:
    if delay_s < 30:
        return "green"
    if delay_s < 90:
        return "amber"
    return "red"


def delay_label(delay_s: float) -> str:
    if delay_s < 0:
        return f"{abs(delay_s):.0f}s zu früh"
    if delay_s < 30:
        return "pünktlich"
    if delay_s < 90:
        return "leichte Verspätung"
    return "erhebliche Verspätung"


def build_feature_row(
    line_name: str,
    stop_name: str,
    hour: int,
    weekday: int,
    month: int,
    temperature: float,
    has_rain: bool,
    has_snow: bool,
    is_holiday: bool,
    has_event: bool,
    stop_lookup: dict,
    stop_line_lookup: dict,
) -> pd.DataFrame:
    stop_info = stop_lookup.get(stop_name, {"district_nr": 1, "n_lines_at_stop": 1, "dwell_time": 0})
    sl_info = stop_line_lookup.get(
        (stop_name, line_name),
        {"is_start_stop": False, "is_end_stop": False, "n_stops_line": 20},
    )

    season = MONTH_TO_SEASON[month]
    is_weekend = weekday >= 5
    is_november = month == 11
    precipitation = 2.0 if has_rain else 0.0
    has_heavy_rain = False
    is_hot = temperature >= 30
    event_weight = 3 if has_event else 0
    event_weight_x_hour = event_weight * hour
    is_late_night_weekend = is_weekend and (hour >= 22 or hour <= 4)

    row = {
        "line_name":           line_name,
        "stop_name":           stop_name,
        "district_nr":         stop_info["district_nr"],
        "temperature":         temperature,
        "precipitation":       precipitation,
        "wind_speed":          5.0,
        "flood_intensity":     0,
        "event_type":          "Konzert" if has_event else "no_event",
        "event_size":          3 if has_event else 0,
        "hour":                hour,
        "weekday":             weekday,
        "month":               month,
        "year":                2025,
        "season":              season,
        "is_weekend":          is_weekend,
        "is_november":         is_november,
        "gtfs_year":           "j24_j25",
        "has_rain":            has_rain,
        "has_heavy_rain":      has_heavy_rain,
        "has_snow":            has_snow,
        "has_flood":           False,
        "is_hot":              is_hot,
        "is_holiday":          is_holiday,
        "has_event":           has_event,
        "event_weight":        event_weight,
        "dwell_time":          stop_info["dwell_time"],
        "n_lines_at_stop":     stop_info["n_lines_at_stop"],
        "n_stops_line":        sl_info["n_stops_line"],
        "is_start_stop":       sl_info["is_start_stop"],
        "is_end_stop":         sl_info["is_end_stop"],
        "event_weight_x_hour": event_weight_x_hour,
        "is_late_night_weekend": is_late_night_weekend,
    }
    df = pd.DataFrame([row])
    cat_cols = ["line_name", "stop_name", "event_type", "season", "gtfs_year"]
    for col in cat_cols:
        df[col] = df[col].astype("category")
    return df


# ─── Explore mode ─────────────────────────────────────────────────────────────

CHART_SECTIONS = [
    {
        "title": "Netzwerk & Linien",
        "charts": [
            ("network.png",                       "Netzwerk-Übersicht: Delay-Profil aller Linien"),
            ("total-network-delay.png",            "Absoluter Delay — netzweite Gesamtübersicht"),
            ("total-network-delay-delta.png",      "Delay-Delta: Abweichung vom Netzwert je Linie"),
            ("total-network-line-delay-dwell.png", "Linien × Dwell-Time — Haltezeit-Einfluss"),
            ("total-network-line-dwell.png",       "Dwell-Time-Verteilung je Linie"),
            ("total-network-otp.png",              "OTP netzweit: 87.0 % On-Time Performance"),
        ],
    },
    {
        "title": "Temporale Muster",
        "charts": [
            ("tempo-day-hours.png",   "Tagesgang: Delay nach Stunde"),
            ("tempo-week-days.png",   "Wochentag-Profil: Mo–So"),
            ("tempo-saison.png",      "Saisonalität: Winter vs. Sommer"),
        ],
    },
    {
        "title": "Meteo-Einfluss",
        "charts": [
            ("meteo-types.png",     "Delay nach Wettertyp"),
            ("meteo-schnee.png",    "Schnee-Einfluss: Stärke × Delay"),
            ("meteo-starkregen.png","Starkregen-Einfluss"),
        ],
    },
    {
        "title": "Events",
        "charts": [
            ("events-timeline.png", "Event-Zeitlinie: Delay-Spitzen rund um Events"),
            ("events-delta.png",    "Event-Delta: +X Sekunden je Event-Typ"),
        ],
    },
    {
        "title": "Geo-Ansichten",
        "charts": [
            ("geo-delay.png",                         "Delay-Heatmap: Zürich City"),
            ("geo-delay-hotspots.png",                "Hotspot-Haltestellen (Top-Risiko)"),
            ("geo-stadtkreise-haltestellen-delay.png","Stadtkreise: mittlerer Delay"),
            ("geo-delay-otp-stadkreise.png",          "OTP nach Stadtkreis"),
        ],
    },
]

INTERACTIVE_MAPS = [
    ("geo-stop-delay-interactive.html",    "Stop-Level: Delay interaktiv (Plotly Mapbox)"),
    ("meteo-weather-impact-map.html",      "Wetter-Impact: räumliche Verteilung"),
    ("network-line-delta-map.html",        "Linien-Delta: welche Linie, wo, wie viel?"),
]
SCHEDULING_MAP = "scheduling-recommendations-map.html"


def render_explore(stop_lookup, stop_line_lookup, all_stops, lines_per_stop):
    st.title("🚋 Zürich Tram Flow — Historische Analyse")
    st.caption(
        "63 Findings aus 94.4 Mio. Datenpunkten · Zeitraum 2023–2025 · Betreiber VBZ Zürich"
    )

    for section in CHART_SECTIONS:
        st.markdown(f"<div class='section-title'>{section['title']}</div>", unsafe_allow_html=True)
        charts = section["charts"]
        cols_per_row = 3
        for i in range(0, len(charts), cols_per_row):
            batch = charts[i : i + cols_per_row]
            cols = st.columns(len(batch))
            for col, (fname, caption) in zip(cols, batch):
                p = IMG / fname
                if p.exists():
                    col.image(str(p), use_container_width=True)
                    col.markdown(f"<div class='chart-caption'>{caption}</div>", unsafe_allow_html=True)
                else:
                    col.info(f"Chart nicht gefunden: {fname}")

    # ── Interaktive Karten ────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Interaktive Karten</div>", unsafe_allow_html=True)
    for fname, label in INTERACTIVE_MAPS:
        p = IMG / fname
        if p.exists():
            with st.expander(f"🗺 {label}", expanded=False):
                st.components.v1.html(p.read_text(encoding="utf-8"), height=560, scrolling=True)
        else:
            st.info(f"Karte noch nicht exportiert: {fname}")

    # ── Scheduling-Empfehlungen ───────────────────────────────────────────────
    sched_p = IMG / SCHEDULING_MAP
    st.markdown("<div class='section-title'>Scheduling-Empfehlungen</div>", unsafe_allow_html=True)
    if sched_p.exists():
        with st.expander("📍 Risiko-Matrix: Welche Stops brauchen Puffer?", expanded=True):
            st.components.v1.html(sched_p.read_text(encoding="utf-8"), height=620, scrolling=True)
    else:
        st.info(
            "Scheduling-Empfehlungskarte wird noch exportiert. "
            "Notebook `06_prediction_7-scheduling_recommendations.ipynb` ausführen, "
            "dann hier neu laden."
        )


# ─── Predict mode ─────────────────────────────────────────────────────────────

def render_predict(stop_lookup, stop_line_lookup, all_stops, lines_per_stop):
    st.title("🎯 Delay-Vorhersage")
    st.caption(
        "LightGBM v1 · 32 Features · MAE 45.7s auf Testjahr 2025 · "
        "Pre-Trip-Use-Case: alle Inputs zum Planungszeitpunkt bekannt"
    )

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("<div class='mode-header'>Fahrt konfigurieren</div>", unsafe_allow_html=True)

        all_lines = sorted(LINE_COLORS.keys())
        line = st.selectbox("Linie", all_lines, index=all_lines.index("11") if "11" in all_lines else 0)

        # Filter stops to those served by selected line
        stops_for_line = sorted(
            [s for s, lines in lines_per_stop.items() if line in [str(l) for l in lines]]
        )
        if not stops_for_line:
            stops_for_line = all_stops
        stop = st.selectbox("Haltestelle", stops_for_line)

        col_hour, col_day = st.columns(2)
        hour = col_hour.selectbox("Stunde", list(range(24)), index=8, format_func=lambda h: f"{h:02d}:00")
        weekday = col_day.selectbox("Wochentag", list(range(7)), format_func=lambda d: WEEKDAY_LABELS[d])

        month = st.selectbox(
            "Monat",
            list(range(1, 13)),
            index=0,
            format_func=lambda m: [
                "Januar", "Februar", "März", "April", "Mai", "Juni",
                "Juli", "August", "September", "Oktober", "November", "Dezember"
            ][m - 1],
        )

        st.markdown("---")
        st.markdown("<div class='mode-header'>Wetter & Kontext</div>", unsafe_allow_html=True)

        col_w1, col_w2 = st.columns(2)
        has_rain     = col_w1.checkbox("Regen")
        has_snow     = col_w2.checkbox("Schnee")
        is_holiday   = col_w1.checkbox("Feiertag")
        has_event    = col_w2.checkbox("Grossveranstaltung")

        temperature = 15
        with st.expander("Temperatur (optional)", expanded=False):
            temperature = st.slider("Temperatur (°C)", min_value=-10, max_value=40, value=15)

        predict_btn = st.button("Delay vorhersagen", type="primary", use_container_width=True)

    with col_result:
        if predict_btn:
            model, meta = load_model()
            feature_df = build_feature_row(
                line_name=line,
                stop_name=stop,
                hour=hour,
                weekday=weekday,
                month=month,
                temperature=temperature,
                has_rain=has_rain,
                has_snow=has_snow,
                is_holiday=is_holiday,
                has_event=has_event,
                stop_lookup=stop_lookup,
                stop_line_lookup=stop_line_lookup,
            )
            feature_df = feature_df[meta["features"]]
            prediction = float(model.predict(feature_df, num_iteration=meta["best_iteration"])[0])

            css_class = delay_color_class(prediction)
            label = delay_label(prediction)

            st.markdown(
                f"""
                <div class='prediction-box'>
                    <div class='prediction-value {css_class}'>{prediction:+.0f}s</div>
                    <div class='prediction-label'>{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### Eingabe-Zusammenfassung")
            context_rows = [
                ("Linie", line),
                ("Haltestelle", stop),
                ("Zeit", f"{hour:02d}:00 · {WEEKDAY_LABELS[weekday]}"),
                ("Monat", f"{month} · Saison {MONTH_TO_SEASON[month]}"),
                ("Wetter", ", ".join(filter(None, [
                    "Regen" if has_rain else "",
                    "Schnee" if has_snow else "",
                    f"{temperature}°C",
                ]))),
                ("Kontext", ", ".join(filter(None, [
                    "Feiertag" if is_holiday else "",
                    "Grossveranstaltung" if has_event else "",
                ])) or "–"),
            ]
            for k, v in context_rows:
                r1, r2 = st.columns([1, 2])
                r1.markdown(f"**{k}**")
                r2.markdown(v)

            stop_info = stop_lookup.get(stop, {})
            sl_info   = stop_line_lookup.get((stop, line), {})
            with st.expander("Stop-Features (automatisch ermittelt)"):
                st.json({
                    "district_nr":    stop_info.get("district_nr"),
                    "n_lines_at_stop": stop_info.get("n_lines_at_stop"),
                    "dwell_time_median_s": stop_info.get("dwell_time"),
                    "is_start_stop":  sl_info.get("is_start_stop"),
                    "is_end_stop":    sl_info.get("is_end_stop"),
                    "n_stops_line":   sl_info.get("n_stops_line"),
                })
        else:
            st.markdown(
                """
                <div style='color:#aaa; margin-top:3rem; text-align:center;'>
                    ← Fahrt konfigurieren, dann<br><strong>„Delay vorhersagen"</strong> klicken
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                **Modell-Kontext**

                LightGBM v1 wurde auf 41.2 Mio. Fahrten (2023–2024) trainiert.
                Alle 32 Features sind zum Planungszeitpunkt bekannt — kein
                `prev_trip_delay` (Kaskadenindikator). Das macht dieses Modell
                zum echten Pre-Trip-Use-Case: Fahrplaner oder Dispatcher kann
                Verspätung vor Fahrtbeginn abschätzen.

                Baseline (Stop-Mittelwert): **50.0s MAE** →
                LightGBM v1: **45.7s MAE** · MBE +8.3s
                """
            )


# ─── Sidebar + routing ────────────────────────────────────────────────────────

def main():
    stop_lookup, stop_line_lookup, all_stops, lines_per_stop = load_lookup()

    with st.sidebar:
        st.markdown("## 🚋 Zürich Tram Flow")
        st.markdown(
            "Verspätungsanalyse + Vorhersage · 2023–2025 · VBZ"
        )
        st.markdown("---")
        mode = st.radio(
            "Modus",
            ["🔍 Erkunden", "🎯 Vorhersagen"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            "**Modell:** LightGBM v1  \n"
            "**MAE:** 45.7s  \n"
            "**Datenpunkte:** 94.4 Mio.  \n"
            "**Findings:** 63"
        )

    if mode == "🔍 Erkunden":
        render_explore(stop_lookup, stop_line_lookup, all_stops, lines_per_stop)
    else:
        render_predict(stop_lookup, stop_line_lookup, all_stops, lines_per_stop)


if __name__ == "__main__" or True:
    main()
